# secure_num_comparsion
Реализация безопасного сравнения двух чисел через MPC без использования CrypTen.

## Принцип работы
Сравнение a > b через вычисление разницы d = a - b:

1. Worker 0 владеет числом a, Worker 1 владеет числом b
2. Числа разделяются на секретные доли между участниками (аддитивное разделение по модулю 2^32)
3. Вычисляется зашифрованная разница d = a - b локально на долях
4. Разница восстанавливается и проверяется знак: a > b ⟺ d > 0

## Запуск

```bash
docker-compose up --build
```

## Вывод программы

```bash
Attaching to ttp, worker0, worker1
worker0  | 2025-10-21 18:48:35,443 [INFO] Rank 0: Starting Multiple Comparison Tests
worker0  | 2025-10-21 18:48:35,443 [INFO] Rank 0: 
worker0  | === Test 1: a=100, b=50, expected a>b = True ===
worker0  | 2025-10-21 18:48:35,474 [INFO] Rank 0: Difference: 50
worker0  | 2025-10-21 18:48:35,476 [INFO] Rank 0: Result: 100 > 50 = True
worker0  | 2025-10-21 18:48:35,476 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 18:48:35,777 [INFO] Rank 0: 
worker0  | === Test 2: a=50, b=100, expected a>b = False ===
worker0  | 2025-10-21 18:48:35,796 [INFO] Rank 0: Difference: -50
worker0  | 2025-10-21 18:48:35,798 [INFO] Rank 0: Result: 50 > 100 = False
worker0  | 2025-10-21 18:48:35,798 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 18:48:36,099 [INFO] Rank 0: 
worker0  | === Test 3: a=100, b=100, expected a>b = False ===
worker0  | 2025-10-21 18:48:36,111 [INFO] Rank 0: Difference: 0
worker0  | 2025-10-21 18:48:36,111 [INFO] Rank 0: Result: 100 > 100 = False
worker0  | 2025-10-21 18:48:36,111 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 18:48:36,414 [INFO] Rank 0: 
worker0  | === Test 4: a=1000, b=999, expected a>b = True ===
worker0  | 2025-10-21 18:48:36,433 [INFO] Rank 0: Difference: 1
worker0  | 2025-10-21 18:48:36,433 [INFO] Rank 0: Result: 1000 > 999 = True
worker0  | 2025-10-21 18:48:36,433 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 18:48:36,737 [INFO] Rank 0: 
worker0  | === Test 5: a=0, b=0, expected a>b = False ===
worker0  | 2025-10-21 18:48:36,750 [INFO] Rank 0: Difference: 0
worker0  | 2025-10-21 18:48:36,754 [INFO] Rank 0: Result: 0 > 0 = False
worker0  | 2025-10-21 18:48:36,754 [INFO] Rank 0: PASSED
worker0  | 2025-10-21 18:48:37,055 [INFO] Rank 0: 
worker0  | === Test 6: a=1, b=0, expected a>b = True ===
worker0  | 2025-10-21 18:48:37,077 [INFO] Rank 0: Difference: 1
worker0  | 2025-10-21 18:48:37,078 [INFO] Rank 0: Result: 1 > 0 = True
worker0  | 2025-10-21 18:48:37,079 [INFO] Rank 0: PASSED
worker0 exited with code 0
worker1 exited with code 0
ttp exited with code 0
```
