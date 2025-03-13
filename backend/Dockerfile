FROM python:3.10-slim

WORKDIR /app
COPY . /app

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Запуск обоих приложений
CMD ["sh", "-c", "python chicken_bot.py & streamlit run streamlit_app.py --server.port=3000"]