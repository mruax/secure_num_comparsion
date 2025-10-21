FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
RUN pip install --no-cache-dir torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu

# Копирование Python файла
COPY mpc.py ./

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1

CMD ["python", "mpc.py", "demo"]
