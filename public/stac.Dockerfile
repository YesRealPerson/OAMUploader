FROM python:3.11-slim

WORKDIR /ap

# Install system dependencies for psycopg and pgstac
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Ensure stac-fastapi.pgstac, uvicorn, brotli-asgi, and python-dotenv are in your requirements.txt
COPY ./public/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application file
COPY ./public/stac.py .

# Expose port (internally)
EXPOSE 8082

# Run the STAC FastAPI server
CMD ["uvicorn", "stac:app", "--host", "0.0.0.0", "--port", "8082"]
# CMD [ "tail", "-f", "/dev/null" ]