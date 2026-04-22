FROM python:3.14

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY static ./static
COPY publicServer.py .

# Expose port, should change later
EXPOSE 12345

# Start server
CMD ["uvicorn", "publicServer:app", "--host", "0.0.0.0", "--port", "12345"]