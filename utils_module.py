"""
Утилиты для MPC протокола
"""
import os
import sys
import logging
import torch.distributed as dist


def setup_logging(rank):
    """Настройка логирования с rank"""
    logger = logging.getLogger()
    logger.setLevel(os.getenv("LOGLEVEL", "INFO"))
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        f'%(asctime)s [%(levelname)s] Rank {rank}: %(message)s'
    )
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
    
    # Настраиваем логирование ДО инициализации distributed
    setup_logging(rank)
    
    # Инициализация process group
    dist.init_process_group(
        backend='gloo',
        init_method=f'tcp://{master_addr}:{master_port}',
        rank=rank,
        world_size=world_size
    )
    
    return rank, world_size
