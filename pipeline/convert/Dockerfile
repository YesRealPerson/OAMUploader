FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*
    
RUN pip install rio-cogeo==7.0.2
COPY script.py .
CMD ["python", "script.py"]