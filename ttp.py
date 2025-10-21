import logging
from typing import Tuple
import torch
import torch.distributed as dist


class TTPServer:
    """
    Trusted Third Party сервер для генерации троек Бивера.
    Генерирует тройки (a, b, c) где c = a AND b и распределяет доли между участниками.
    """
    
    def __init__(self, rank: int, world_size: int, num_workers: int = 2):
        self.rank = rank
        self.world_size = world_size
        self.num_workers = num_workers
        logging.info("TTP Server initialized")
    
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
        
        # Разделяем тройки между worker'ами
        worker0_triples = []
        worker1_triples = []
        
        for triple in triples:
            a, b, c = triple
            
            # XOR sharing для двоичных значений
            a0 = torch.randint(0, 2, (1,)).item()
            b0 = torch.randint(0, 2, (1,)).item()
            c0 = torch.randint(0, 2, (1,)).item()
            
            a1 = a ^ a0
            b1 = b ^ b0
            c1 = c ^ c0
            
            worker0_triples.append([a0, b0, c0])
            worker1_triples.append([a1, b1, c1])
        
        logging.info("Beaver triples generated, ready to distribute")
        
        # Отправляем тройки worker'ам по запросу
        triple_idx = 0
        while triple_idx < num_triples:
            for worker_rank in range(self.num_workers):
                if triple_idx >= num_triples:
                    break
                
                # Отправляем тройку worker'у
                if worker_rank == 0:
                    triple_tensor = torch.tensor(
                        worker0_triples[triple_idx], 
                        dtype=torch.int64
                    )
                else:
                    triple_tensor = torch.tensor(
                        worker1_triples[triple_idx], 
                        dtype=torch.int64
                    )
                
                dist.send(triple_tensor, dst=worker_rank)
                logging.debug(f"Sent triple {triple_idx} to worker {worker_rank}")
            
            triple_idx += 1
        
        logging.info("All triples distributed")
