FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir rio-cogeo==7.0.2
RUN pip install --no-cache-dir rasterio==1.5.0
RUN pip install --no-cache-dir pystac==1.14.3
COPY script.py .
CMD ["python", "script.py"]