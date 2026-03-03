FROM python:3.12

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy required files
COPY publicServer.py ./

# Expose port, should change later
EXPOSE 8080

# Start server
CMD ["uvicorn", ""]