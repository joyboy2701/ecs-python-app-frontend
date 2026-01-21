FROM python:3.11-slim

WORKDIR /app

# Install curl for better health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install fastapi uvicorn python-multipart

COPY app.py .

VOLUME ["/data"]

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]