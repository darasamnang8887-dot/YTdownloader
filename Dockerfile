# Use official Python slim image for small footprint
FROM python:3.10-slim

# Install system dependencies including FFmpeg for cloud video merging
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy dependencies first for faster caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Hugging Face Spaces defaults to exposing port 7860
EXPOSE 7860

# Command to run under the high-performance Gunicorn WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "web_app:app"]
