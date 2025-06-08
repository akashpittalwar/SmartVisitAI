# Dockerfile

# 1) Use a slim Python base image for fast startup and minimal size
FROM python:3.10-slim as build

# Install build-essential if needed (not strictly necessary here)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# 2) Copy requirements and install dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 3) Copy the rest of the application code
COPY . .

# 4) Expose port 8080 for Cloud Run
EXPOSE 8080

# 5) Run the app with Gunicorn (2 workers for concurrency)
#    --bind 0.0.0.0:8080  ensures Cloud Run can route traffic.
CMD exec gunicorn --bind 0.0.0.0:8080 --workers 2 app:app
