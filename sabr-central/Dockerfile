FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

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

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PORT 10000

CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--chdir", "sabr-central", "app:app"]
