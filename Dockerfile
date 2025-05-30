FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port and set environment
ENV PORT 5000
EXPOSE 5000

# Start the Flask application
CMD ["python", "main.py"]