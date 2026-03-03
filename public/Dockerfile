FROM python:3.14

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port, should change later
EXPOSE 8080

# Start server
CMD ["uvicorn", "publicServer:app", "--port", "8080", "--host=0.0.0.0", "--reload"]