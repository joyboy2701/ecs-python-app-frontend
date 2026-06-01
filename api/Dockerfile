FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --only-binary=:all: \
    fastapi==0.115.6 \
    httpx==0.28.1 \
    python-multipart==0.0.20 \
    uvicorn==0.34.0

COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]