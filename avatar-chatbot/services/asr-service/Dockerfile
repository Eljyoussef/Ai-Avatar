FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*
COPY services/asr-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/asr-service/app/ ./app/
COPY shared/ ./shared/
CMD ["python3", "-m", "app.main"]