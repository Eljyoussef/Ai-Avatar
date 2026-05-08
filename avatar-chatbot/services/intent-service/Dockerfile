FROM python:3.11-slim
WORKDIR /app
COPY services/intent-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/intent-service/app ./app
COPY shared /shared
CMD ["python3", "-m", "app.main"]