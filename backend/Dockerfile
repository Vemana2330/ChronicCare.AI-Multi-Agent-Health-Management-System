# FastAPI Backend Dockerfile
FROM python:3.11.7

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y gcc

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]