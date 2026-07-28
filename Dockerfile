FROM python:3.11-slim

# Install system dependencies required by WeasyPrint and image libraries
RUN apt-get update \
     && apt-get install -y --no-install-recommends \
         build-essential \
         ca-certificates \
         wget \
         gnupg \
         libpango-1.0-0 \
         libpangocairo-1.0-0 \
         libcairo2 \
         libgdk-pixbuf2.0-0 \
         libjpeg62-turbo \
         libffi-dev \
         libxml2 \
         libxslt1.1 \
         shared-mime-info \
         fonts-dejavu-core \
         fontconfig \
     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy top-level requirements and install
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy repository
COPY . /app

# Render provides the $PORT env var
ENV PORT 10000

# Default command: use gunicorn and change to the inner app dir
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--chdir", "sabr-central/sabr-central", "app:app"]
