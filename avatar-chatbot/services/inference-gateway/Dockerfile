FROM python:3.11-slim
WORKDIR /app
COPY services/inference-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/inference-gateway/app ./app
COPY shared /shared
CMD ["python3", "-m", "app.main"]