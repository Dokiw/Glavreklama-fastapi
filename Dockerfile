# Базовый образ Python
FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY ./app ./app

# Открываем порт (тот, что у тебя в main.py)
EXPOSE 8080

# Запуск приложения
# Вариант 1: через uvicorn напрямую
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

# Вариант 2: через сам main.py (если оставлять uvicorn.run в коде)
# CMD ["python", "-m", "app.main"]
