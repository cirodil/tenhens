FROM python:3.10-slim
WORKDIR /app
COPY chicken_bot.py requirements.txt ./
COPY data/ ./data/
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "chicken_bot.py"]