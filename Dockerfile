FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
    
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN useradd -m appuser

# Copy everything else
COPY . .

# Change ownership of the application directory
RUN chown -R appuser:appuser /app

# Environment variables
ENV FLASK_APP=main.py
ENV PYTHONUNBUFFERED=1

# Switch to the non-root user
USER appuser

CMD ["python", "main.py"]
