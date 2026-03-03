FROM python:3.14

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY public/static ./static
COPY public/publicServer.py ./

RUN mkdir -p /mnt/temporary
RUN ln -s /mnt/temporary /temporary
COPY temporary/testfile.txt /mnt/temporary/testfile.txt

# Expose port, should change later
EXPOSE 8080

# Start server
CMD ["uvicorn", "publicServer:app", "--port", "8080", "--host=0.0.0.0"]