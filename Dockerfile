# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем entrypoint скрипт и делаем его исполняемым
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Копируем весь код приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/data /app/logs /app/instance

# Устанавливаем переменные окружения
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Экспонируем порт
EXPOSE 5000

# Health check (временно отключаем до добавления health endpoint)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#     CMD curl -f http://localhost:5000/health || exit 1

# Entrypoint для инициализации
ENTRYPOINT ["/entrypoint.sh"]

# Команда запуска с Gunicorn для production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--preload", "run:app"] 