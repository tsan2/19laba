# Используем Python 3.11
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Копируем весь проект
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Порт, на котором Flask будет слушать
EXPOSE 5000

# Команда запуска
CMD ["python", "app.py"]