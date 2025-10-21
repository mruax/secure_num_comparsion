"""
Запуск TTP сервера
"""
import logging
import torch.distributed as dist

from utils import init_distributed
from ttp import TTPServer


def main():
    """Запуск TTP сервера"""
    rank, world_size = init_distributed()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting TTP Server")
    
    # Количество worker'ов = world_size - 1 (минус сам TTP)
    num_workers = world_size - 1
    
    ttp = TTPServer(rank=rank, world_size=world_size, num_workers=num_workers)
    
    # Генерируем достаточно троек для тестов
    ttp.run(num_triples=100)
    
    logger.info("TTP Server finished")
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
