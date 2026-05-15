FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all worker source files
COPY . .

# Run the worker
CMD ["python", "worker.py"]
