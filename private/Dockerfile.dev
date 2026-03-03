FROM python:3.14

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port, should change later
EXPOSE 7070

# Start server
CMD ["uvicorn", "internalServer:app", "--port", "7070", "--host=0.0.0.0", "--reload"]