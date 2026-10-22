# Multi-stage production container for Cloud Resource Scheduler
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose web port
EXPOSE 5000

ENV FLASK_ENV=production
ENV DEBUG=False
ENV USE_SQLITE_FALLBACK=True
ENV PORT=5000

CMD ["python", "run.py"]
