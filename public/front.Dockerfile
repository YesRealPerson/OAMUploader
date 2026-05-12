FROM python:3.11-slim

WORKDIR /app

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
# Ensure boto3, fastapi, uvicorn, httpx, kubernetes, python-jose, and python-dotenv are in your requirements.txt
COPY ./public/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ./public/front.py .
COPY ./public/static/ ./static/

# Expose the public port
EXPOSE 12345

# Run the FastAPI server
CMD ["uvicorn", "front:app", "--host", "0.0.0.0", "--port", "12345"]