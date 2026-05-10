FROM python:3.11-slim
WORKDIR /app
COPY services/memory-service/requirements.txt .
RUN pip install --no-cache-dir --timeout=300 --retries=5 -r requirements.txt
COPY services/memory-service/app ./app
COPY shared /shared
CMD ["python3", "-m", "app.main"]