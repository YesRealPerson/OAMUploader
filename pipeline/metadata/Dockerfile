FROM python:3.12-slim
RUN pip install rio-cogeo==7.0.2
RUN pip install rasterio==1.5.0
RUN pip install pystac==1.14.3
COPY script.py .
CMD ["python", "script.py"]