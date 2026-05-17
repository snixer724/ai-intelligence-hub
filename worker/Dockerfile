FROM mcr.microsoft.com/playwright/python:v1.59.0-noble

# Force Python to flush logs to the terminal immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all worker source files
COPY . .

# Run the worker
CMD ["python", "worker.py"]
