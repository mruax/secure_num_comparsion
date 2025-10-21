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
    
    # Генерируем тройки (но не отправляем автоматически)
    logger.info("Generating Beaver triples...")
    triples = [ttp.generate_beaver_triple() for _ in range(100)]
    logger.info(f"Generated {len(triples)} Beaver triples and ready to serve")
    
    # Ждём завершения worker'ов
    logger.info("TTP Server waiting for workers to complete...")
    
    # Простой барьер - ждём пока worker'ы не завершатся
    try:
        dist.barrier()
    except:
        pass  # Worker'ы уже завершились
    
    logger.info("TTP Server finished")
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
    