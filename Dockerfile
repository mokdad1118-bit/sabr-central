FROM python:3.11-slim

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required by WeasyPrint and image libraries
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       ca-certificates \
       wget \
       gnupg \
       pkg-config \
       libpango-1.0-0 \
       libpangocairo-1.0-0 \
       libcairo2 \
       libcairo2-dev \
       libgdk-pixbuf2.0-0 \
       libjpeg-dev \
       libffi-dev \
       libxml2 \
       libxslt1.1 \
       shared-mime-info \
       fonts-dejavu-core \
       fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies first to leverage Docker cache
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Expose port (Render sets $PORT at runtime)
ENV PORT 10000

# Use gunicorn to serve the Flask app; the app lives in sabr-central/sabr-central/app.py
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --chdir sabr-central/sabr-central app:app"]
