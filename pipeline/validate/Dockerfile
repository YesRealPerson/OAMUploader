FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir rasterio==1.5.0

COPY script.py .
CMD ["python", "script.py"]