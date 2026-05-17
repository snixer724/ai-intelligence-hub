FROM mcr.microsoft.com/playwright/python:v1.59.0-noble

# Force Python to flush logs to the terminal immediately
ENV PYTHONUNBUFFERED=1

# Install Node.js for MCP
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download chrome dependencies for Playwright
RUN playwright install --with-deps chrome

# Copy all worker source files
COPY . .

# Run the worker
CMD ["python", "worker.py"]
