# Используем официальный образ Python 3.10 (именно 3.10!)
FROM python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости, необходимые для сборки numpy/pandas
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВЕСЬ ваш проект в контейнер
COPY . .

# Команда для запуска приложения
# Render сам подставит переменную PORT
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
