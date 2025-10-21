import time
import logging
import argparse
import torch.distributed as dist

from utils import init_distributed
from protocol import MPCComparison


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
    parser.add_argument(
        "task", 
        choices=["demo", "tests"],
        help="Task to run"
    )
    args = parser.parse_args()
    
    if args.task == "demo":
        run_simple_demo()
    elif args.task == "tests":
        run_multiple_tests()


if __name__ == "__main__":
    main()
