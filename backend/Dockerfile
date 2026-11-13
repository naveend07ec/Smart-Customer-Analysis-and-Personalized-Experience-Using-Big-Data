FROM python:3.11-slim

WORKDIR /app

# Install Java 17/8 for PySpark runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends default-jre-headless procps && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5000

CMD ["python", "backend/app.py"]
