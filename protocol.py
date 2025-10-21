"""
MPC протокол сравнения чисел
"""
from typing import Optional
import torch
import torch.distributed as dist
from mpc_secrets import SecretShare


class MPCComparison:
    """
    Протокол сравнения чисел через MPC.
    Сравнивает a > b путем вычисления d = a - b и проверки d > 0
    """
    
    def __init__(self, rank: int, world_size: int, bit_length: int = 32):
        self.rank = rank
        self.world_size = world_size
        self.bit_length = bit_length
        self.modulus = 2**32  # Модуль для арифметики
        
        # Определяем количество worker'ов (исключая TTP если есть)
        # Если world_size=3, то последний rank - это TTP
        self.num_workers = 2 if world_size == 3 else world_size
    
    def share_secret(self, value: Optional[int], src: int) -> SecretShare:
        """Разделение секрета между участниками (только worker'ы)"""
        if self.rank == src:
            # Генерируем случайные доли для всех worker'ов кроме последнего
            shares = []
            total = 0
            for i in range(self.num_workers - 1):
                random_share = int(torch.randint(0, 2**31, (1,)).item())
                shares.append(random_share)
                total = (total + random_share) % self.modulus
            
            # Последняя доля = value - сумма остальных
            last_share = (value - total) % self.modulus
            shares.append(last_share)
            
            # Отправляем доли только worker'ам (rank 0 и 1)
            for i in range(self.num_workers):
                if i != src:
                    tensor = torch.tensor([shares[i]], dtype=torch.int64)
                    dist.send(tensor, dst=i)
            
            return SecretShare(shares[src], self.modulus)
        else:
            # Получаем свою долю (только если мы worker)
            tensor = torch.tensor([0], dtype=torch.int64)
            dist.recv(tensor, src=src)
            return SecretShare(int(tensor.item()), self.modulus)
    
    def reconstruct_secret(self, share: SecretShare) -> int:
        """Восстановление секрета из долей (только worker'ы)"""
        # Собираем все доли на rank 0
        if self.rank == 0:
            shares = [share.share]
            # Получаем доли только от других worker'ов
            for i in range(1, self.num_workers):
                tensor = torch.tensor([0], dtype=torch.int64)
                dist.recv(tensor, src=i)
                shares.append(int(tensor.item()))
            
            # Суммируем доли
            result = sum(shares) % self.modulus
            
            # Корректируем если результат слишком большой (был отрицательным)
            if result > self.modulus // 2:
                result = result - self.modulus
            
            return result
        else:
            # Отправляем долю на rank 0 (только если мы worker)
            tensor = torch.tensor([share.share], dtype=torch.int64)
            dist.send(tensor, dst=0)
            return None
    
    def to_binary_shares(self, arith_share: SecretShare) -> list:
        """Конвертация арифметической доли в двоичные доли"""
        from secrets import BinaryShare
        bits = []
        value = arith_share.share
        for i in range(self.bit_length):
            bit = (value >> i) & 1
            bits.append(BinaryShare(bit))
        return bits
    
    def get_beaver_triple(self) -> tuple:
        """Получение тройки Бивера от TTP"""
        # Получаем от TTP (последний rank в мире)
        ttp_rank = self.world_size - 1
        tensor = torch.zeros(3, dtype=torch.int64)
        dist.recv(tensor, src=ttp_rank)
        return tuple(tensor.tolist())
    