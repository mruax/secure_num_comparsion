import torch
import torch.distributed as dist
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class SecretShare:
    """Класс для арифметического разделения секретов по модулю"""

    def __init__(self, share: int, modulus: int = 2 ** 64):
        self.share = share % modulus
        self.modulus = modulus

    def __add__(self, other):
        if isinstance(other, SecretShare):
            return SecretShare((self.share + other.share) % self.modulus, self.modulus)
        return SecretShare((self.share + other) % self.modulus, self.modulus)

    def __sub__(self, other):
        if isinstance(other, SecretShare):
            return SecretShare((self.share - other.share) % self.modulus, self.modulus)
        return SecretShare((self.share - other) % self.modulus, self.modulus)

    def __mul__(self, scalar: int):
        """Умножение на публичную константу"""
        return SecretShare((self.share * scalar) % self.modulus, self.modulus)


class BinaryShare:
    """Класс для двоичного разделения секретов (XOR-based)"""

    def __init__(self, share: int):
        self.share = share

    def __xor__(self, other):
        if isinstance(other, BinaryShare):
            return BinaryShare(self.share ^ other.share)
        return BinaryShare(self.share ^ other)


class MPCComparison:
    """
    Протокол сравнения чисел через MPC.
    Сравнивает a > b путем вычисления d = a - b и проверки d > 0
    """

    def __init__(self, rank: int, world_size: int, bit_length: int = 32):
        self.rank = rank
        self.world_size = world_size
        self.bit_length = bit_length
        self.modulus = 2 ** 64

    def share_secret(self, value: Optional[int], src: int) -> SecretShare:
        """Разделение секрета между участниками"""
        if self.rank == src:
            # Генерируем случайные доли для всех кроме последнего
            shares = []
            total = 0
            for i in range(self.world_size - 1):
                random_share = torch.randint(0, self.modulus, (1,)).item()
                shares.append(random_share)
                total = (total + random_share) % self.modulus

            # Последняя доля = value - сумма остальных
            last_share = (value - total) % self.modulus
            shares.append(last_share)

            # Отправляем доли участникам
            for i in range(self.world_size):
                if i != src:
                    tensor = torch.tensor([shares[i]], dtype=torch.long)
                    dist.send(tensor, dst=i)

            return SecretShare(shares[src], self.modulus)
        else:
            # Получаем свою долю
            tensor = torch.tensor([0], dtype=torch.long)
            dist.recv(tensor, src=src)
            return SecretShare(tensor.item(), self.modulus)

    def reconstruct_secret(self, share: SecretShare) -> int:
        """Восстановление секрета из долей"""
        # Собираем все доли на rank 0
        if self.rank == 0:
            shares = [share.share]
            for i in range(1, self.world_size):
                tensor = torch.tensor([0], dtype=torch.long)
                dist.recv(tensor, src=i)
                shares.append(tensor.item())

            # Суммируем доли
            result = sum(shares) % self.modulus

            # Корректируем если результат слишком большой (был отрицательным)
            if result > self.modulus // 2:
                result -= self.modulus

            return result
        else:
            tensor = torch.tensor([share.share], dtype=torch.long)
            dist.send(tensor, dst=0)
            return None

    def to_binary_shares(self, arith_share: SecretShare) -> list:
        """Конвертация арифметической доли в двоичные доли"""
        # Упрощенная версия: берем биты арифметической доли
        bits = []
        value = arith_share.share
        for i in range(self.bit_length):
            bit = (value >> i) & 1
            bits.append(BinaryShare(bit))
        return bits

    def secure_and(self, x_bit: BinaryShare, y_bit: BinaryShare,
                   beaver_triple: Tuple[int, int, int]) -> BinaryShare:
        """
        Безопасное AND с использованием тройки Бивера.
        beaver_triple = (a, b, c) где c = a AND b
        """
        a, b, c = beaver_triple

        # Вычисляем e = x XOR a, f = y XOR b
        e_share = x_bit.share ^ a
        f_share = y_bit.share ^ b

        # Открываем e и f
        e = self._open_binary(e_share)
        f = self._open_binary(f_share)

        # Вычисляем z = c XOR (e AND b) XOR (f AND a) XOR (e AND f)
        if self.rank == 0:
            z_share = c ^ (e & b) ^ (f & a) ^ (e & f)
        else:
            z_share = c ^ (e & b) ^ (f & a)

        return BinaryShare(z_share)

    def _open_binary(self, bit_share: int) -> int:
        """Открытие двоичной доли"""
        # Обмениваемся долями
        if self.rank == 0:
            shares = [bit_share]
            for i in range(1, self.world_size):
                tensor = torch.tensor([0], dtype=torch.long)
                dist.recv(tensor, src=i)
                shares.append(tensor.item())

            result = 0
            for s in shares:
                result ^= s

            # Отправляем результат всем
            for i in range(1, self.world_size):
                tensor = torch.tensor([result], dtype=torch.long)
                dist.send(tensor, dst=i)

            return result
        else:
            tensor = torch.tensor([bit_share], dtype=torch.long)
            dist.send(tensor, dst=0)

            tensor = torch.tensor([0], dtype=torch.long)
            dist.recv(tensor, src=0)
            return tensor.item()

    def get_beaver_triple(self) -> Tuple[int, int, int]:
        """Получение тройки Бивера от TTP"""
        # Получаем от TTP (rank 2)
        ttp_rank = 2
        tensor = torch.zeros(3, dtype=torch.long)
        dist.recv(tensor, src=ttp_rank)
        return tuple(tensor.tolist())

    def compare_greater(self, a_share: SecretShare, b_share: SecretShare,
                        beaver_triples: list) -> BinaryShare:
        """
        Сравнение a > b через разницу d = a - b
        Проверяем знаковый бит d
        """
        # Вычисляем d = a - b
        d_share = a_share - b_share

        # Конвертируем в двоичные доли
        d_bits = self.to_binary_shares(d_share)

        # Проверяем знаковый бит (старший бит)
        # Если знаковый бит = 0, то d > 0 (a > b)
        # Если знаковый бит = 1, то d < 0 (a < b)
        sign_bit = d_bits[self.bit_length - 1]

        # Инвертируем знаковый бит: result = NOT sign_bit = 1 XOR sign_bit
        result = BinaryShare(1 ^ sign_bit.share)

        return result

    def open_comparison_result(self, result_share: BinaryShare) -> Optional[bool]:
        """Открытие результата сравнения"""
        result_bit = self._open_binary(result_share.share)
        if self.rank == 0:
            return bool(result_bit)
        return None
