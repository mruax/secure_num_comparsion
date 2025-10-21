# secure_num_comparsion
Реализация безопасного сравнения двух чисел через MPC без использования CrypTen.

## Принцип работы
Сравнение a > b через вычисление разницы d = a - b:

1. Worker 0 владеет числом a, Worker 1 владеет числом b
2. Числа разделяются на секретные доли между участниками (аддитивное разделение по модулю 2^32)
3. Вычисляется зашифрованная разница d = a - b локально на долях
4. Разница восстанавливается и проверяется знак: a > b и d > 0

## Запуск

```bash
docker-compose up --build
```

## Вывод программы

```bash
Attaching to ttp, worker0, worker1
worker0  | 2025-10-21 19:00:03,714 [INFO] Rank 0: Added key: store_based_barrier_key:1 to store for rank: 0
worker1  | 2025-10-21 19:00:03,749 [INFO] Rank 1: Added key: store_based_barrier_key:1 to store for rank: 1
ttp      | 2025-10-21 19:00:03,755 [INFO] Rank 2: Added key: store_based_barrier_key:1 to store for rank: 2
ttp      | 2025-10-21 19:00:03,759 [INFO] Rank 2: Rank 2: Completed store-based barrier for key:store_based_barrier_key:1 with 3 nodes.
ttp      | 2025-10-21 19:00:03,759 [INFO] Rank 2: Starting TTP Server
ttp      | 2025-10-21 19:00:03,759 [INFO] Rank 2: TTP Server initialized
ttp      | 2025-10-21 19:00:03,759 [INFO] Rank 2: Generating Beaver triples...
ttp      | 2025-10-21 19:00:03,769 [INFO] Rank 2: Generated 100 Beaver triples and ready to serve
worker0  | 2025-10-21 19:00:03,755 [INFO] Rank 0: Rank 0: Completed store-based barrier for key:store_based_barrier_key:1 with 3 nodes.
worker0  | 2025-10-21 19:00:03,760 [INFO] Rank 0: Starting Multiple Comparison Tests
worker0  | 2025-10-21 19:00:03,760 [INFO] Rank 0: 
ttp      | 2025-10-21 19:00:03,769 [INFO] Rank 2: TTP Server waiting for workers to complete...
worker1  | 2025-10-21 19:00:03,776 [INFO] Rank 1: Rank 1: Completed store-based barrier for key:store_based_barrier_key:1 with 3 nodes.

worker1  | 2025-10-21 19:00:03,776 [INFO] Rank 1: Starting Multiple Comparison Tests
worker0  | === Test 1: a=100, b=50, expected a>b = True ===
worker0  | 2025-10-21 19:00:03,797 [INFO] Rank 0: Difference: 50
worker0  | 2025-10-21 19:00:03,798 [INFO] Rank 0: Result: 100 > 50 = True
worker0  | 2025-10-21 19:00:03,798 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 19:00:04,100 [INFO] Rank 0: 
worker0  | === Test 2: a=50, b=100, expected a>b = False ===
worker0  | 2025-10-21 19:00:04,114 [INFO] Rank 0: Difference: -50
worker0  | 2025-10-21 19:00:04,114 [INFO] Rank 0: Result: 50 > 100 = False
worker0  | 2025-10-21 19:00:04,114 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 19:00:04,418 [INFO] Rank 0: 
worker0  | === Test 3: a=100, b=100, expected a>b = False ===
worker0  | 2025-10-21 19:00:04,425 [INFO] Rank 0: Difference: 0
worker0  | 2025-10-21 19:00:04,425 [INFO] Rank 0: Result: 100 > 100 = False
worker0  | 2025-10-21 19:00:04,425 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 19:00:04,727 [INFO] Rank 0: 
worker0  | === Test 4: a=1000, b=999, expected a>b = True ===
worker0  | 2025-10-21 19:00:04,751 [INFO] Rank 0: Difference: 1
worker0  | 2025-10-21 19:00:04,753 [INFO] Rank 0: Result: 1000 > 999 = True
worker0  | 2025-10-21 19:00:04,753 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 19:00:05,055 [INFO] Rank 0: 
worker0  | === Test 5: a=0, b=0, expected a>b = False ===
worker0  | 2025-10-21 19:00:05,078 [INFO] Rank 0: Difference: 0
worker0  | 2025-10-21 19:00:05,080 [INFO] Rank 0: Result: 0 > 0 = False
worker0  | 2025-10-21 19:00:05,080 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 19:00:05,383 [INFO] Rank 0: 
worker0  | === Test 6: a=1, b=0, expected a>b = True ===
worker0  | 2025-10-21 19:00:05,404 [INFO] Rank 0: Difference: 1
worker0  | 2025-10-21 19:00:05,404 [INFO] Rank 0: Result: 1 > 0 = True
worker0  | 2025-10-21 19:00:05,404 [INFO] Rank 0: PASSED
ttp      | 2025-10-21 19:00:05,745 [INFO] Rank 2: TTP Server finished
worker1 exited with code 0
worker0 exited with code 0
ttp exited with code 0
```

Также исправил баг, что TTP завершался некорректно (теперь корректно ожидает воркеров).
