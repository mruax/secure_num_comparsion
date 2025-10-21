"""
MPC протокол сравнения чисел - всё в одном файле
"""
import os
import sys
import time
import logging
import argparse
from typing import Tuple, Optional
import torch
import torch.distributed as dist


class SecretShare:
    """Класс для арифметического разделения секретов по модулю"""
    
    def __init__(self, share: int, modulus: int = 2**32):
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
        self.modulus = 2**32  # Модуль
    
    def share_secret(self, value: Optional[int], src: int) -> SecretShare:
        """Разделение секрета между участниками"""
        if self.rank == src:
            # Генерируем случайные доли для всех кроме последнего
            shares = []
            total = 0
            for i in range(self.world_size - 1):
                random_share = int(torch.randint(0, 2**31, (1,)).item())
                shares.append(random_share)
                total = (total + random_share) % self.modulus
            
            # Последняя доля = value - сумма остальных
            last_share = (value - total) % self.modulus
            shares.append(last_share)
            
            # Отправляем доли участникам
            for i in range(self.world_size):
                if i != src:
                    tensor = torch.tensor([shares[i]], dtype=torch.int64)
                    dist.send(tensor, dst=i)
            
            return SecretShare(shares[src], self.modulus)
        else:
            # Получаем свою долю
            tensor = torch.tensor([0], dtype=torch.int64)
            dist.recv(tensor, src=src)
            return SecretShare(int(tensor.item()), self.modulus)
    
    def reconstruct_secret(self, share: SecretShare) -> int:
        """Восстановление секрета из долей"""
        # Собираем все доли на rank 0
        if self.rank == 0:
            shares = [share.share]
            for i in range(1, self.world_size):
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
            tensor = torch.tensor([share.share], dtype=torch.int64)
            dist.send(tensor, dst=0)
            return None


class TTPServer:
    """
    Trusted Third Party сервер для генерации троек Бивера.
    """
    
    def __init__(self, rank: int, world_size: int, num_workers: int = 2):
        self.rank = rank
        self.world_size = world_size
        self.num_workers = num_workers
        logging.info(f"TTP Server initialized")
    
    def generate_beaver_triple(self) -> Tuple[int, int, int]:
        """Генерация одной тройки Бивера"""
        a = torch.randint(0, 2, (1,)).item()
        b = torch.randint(0, 2, (1,)).item()
        c = a & b
        return (a, b, c)
    
    def run(self, num_triples: int = 100):
        """Основной цикл TTP сервера"""
        logging.info(f"Generating {num_triples} Beaver triples")
        
        # Предгенерируем тройки
        triples = [self.generate_beaver_triple() for _ in range(num_triples)]
        
        # Разделяем тройки между воркерами
        worker0_triples = []
        worker1_triples = []
        
        for triple in triples:
            a, b, c = triple
            
            # XOR sharing
            a0 = torch.randint(0, 2, (1,)).item()
            b0 = torch.randint(0, 2, (1,)).item()
            c0 = torch.randint(0, 2, (1,)).item()
            
            a1 = a ^ a0
            b1 = b ^ b0
            c1 = c ^ c0
            
            worker0_triples.append([a0, b0, c0])
            worker1_triples.append([a1, b1, c1])
        
        logging.info("Beaver triples generated, ready to distribute")
        
        # Отправляем тройки воркерам по запросу
        triple_idx = 0
        while triple_idx < num_triples:
            for worker_rank in range(self.num_workers):
                if triple_idx >= num_triples:
                    break
                
                # Отправляем тройку воркеру
                if worker_rank == 0:
                    triple_tensor = torch.tensor(worker0_triples[triple_idx], dtype=torch.long)
                else:
                    triple_tensor = torch.tensor(worker1_triples[triple_idx], dtype=torch.long)
                
                dist.send(triple_tensor, dst=worker_rank)
            
            triple_idx += 1
        
        logging.info("All triples distributed")


def setup_logging(rank):
    """Настройка логирования c rank"""
    logger = logging.getLogger()
    logger.setLevel(os.getenv("LOGLEVEL", "INFO"))
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(f'%(asctime)s [%(levelname)s] Rank {rank}: %(message)s')
    handler.setFormatter(formatter)
    
    logger.handlers.clear()
    logger.addHandler(handler)
    
    return logger


def init_distributed():
    """Инициализация torch.distributed"""
    rank = int(os.environ['RANK'])
    world_size = int(os.environ['WORLD_SIZE'])
    master_addr = os.environ['MASTER_ADDR']
    master_port = os.environ['MASTER_PORT']
    
    # Настраиваем логирование до инициализации distributed
    setup_logging(rank)
    
    # Инициализация process group
    dist.init_process_group(
        backend='gloo',
        init_method=f'tcp://{master_addr}:{master_port}',
        rank=rank,
        world_size=world_size
    )
    
    return rank, world_size


def run_ttp():
    """Запуск TTP сервера"""
    rank, world_size = init_distributed()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting TTP Server")
    
    ttp = TTPServer(rank=rank, world_size=world_size, num_workers=2)
    ttp.run(num_triples=100)
    
    logger.info("TTP Server finished")
    dist.destroy_process_group()


def run_simple_demo():
    """Упрощенная демонстрация сравнения"""
    rank, world_size = init_distributed()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Simple Comparison Demo")
    
    # Тестовые значения
    a_val = 42
    b_val = 17
    
    logger.info(f"Will compare a={a_val} and b={b_val}")
    
    # Создаем MPC объект
    mpc = MPCComparison(rank=rank, world_size=world_size, bit_length=16)
    
    # Разделяем секреты
    if rank == 0:
        a_share = mpc.share_secret(a_val, src=0)
        b_share = mpc.share_secret(None, src=1)
        logger.info(f"My shares: a={a_share.share}, b={b_share.share}")
    else:
        a_share = mpc.share_secret(None, src=0)
        b_share = mpc.share_secret(b_val, src=1)
        logger.info(f"My shares: a={a_share.share}, b={b_share.share}")
    
    # Вычисляем разницу d = a - b
    d_share = a_share - b_share
    logger.info(f"Difference share d: {d_share.share}")
    
    # Восстанавливаем разницу
    d_reconstructed = mpc.reconstruct_secret(d_share)
    
    if rank == 0:
        logger.info(f"Reconstructed difference: {d_reconstructed}")
        logger.info(f"Expected difference: {a_val - b_val}")
        
        # Проверяем знак
        is_positive = d_reconstructed > 0
        logger.info(f"Result: {a_val} > {b_val} = {is_positive}")
        
        if is_positive == (a_val > b_val):
            logger.info("Test PASSED")
        else:
            logger.error("Test FAILED")
    
    dist.destroy_process_group()


def run_multiple_tests():
    """Множественные тесты сравнения"""
    rank, world_size = init_distributed()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Multiple Comparison Tests")
    
    test_cases = [
        (100, 50, True),
        (50, 100, False),
        (100, 100, False),
        (1000, 999, True),
        (0, 0, False),
        (1, 0, True),
    ]
    
    mpc = MPCComparison(rank=rank, world_size=world_size, bit_length=32)
    
    for idx, (a_val, b_val, expected) in enumerate(test_cases):
        if rank == 0:
            logger.info(f"\n=== Test {idx+1}: a={a_val}, b={b_val}, expected a>b = {expected} ===")
        
        # Разделяем секреты
        if rank == 0:
            a_share = mpc.share_secret(a_val, src=0)
            b_share = mpc.share_secret(None, src=1)
        else:
            a_share = mpc.share_secret(None, src=0)
            b_share = mpc.share_secret(b_val, src=1)
        
        # Вычисляем разницу
        d_share = a_share - b_share
        d_reconstructed = mpc.reconstruct_secret(d_share)
        
        if rank == 0:
            result = d_reconstructed > 0
            logger.info(f"Difference: {d_reconstructed}")
            logger.info(f"Result: {a_val} > {b_val} = {result}")
            
            if result == expected:
                logger.info("PASSED")
            else:
                logger.error(f"FAILED: expected {expected}, got {result}")
        
        time.sleep(0.3)
    
    dist.destroy_process_group()


def main():
    parser = argparse.ArgumentParser(description="MPC Comparison Worker")
    parser.add_argument("task", 
                       choices=["ttp", "demo", "tests"],
                       help="Task to run")
    args = parser.parse_args()
    
    if args.task == "ttp":
        run_ttp()
    elif args.task == "demo":
        run_simple_demo()
    elif args.task == "tests":
        run_multiple_tests()

if __name__ == "__main__":
    main()
