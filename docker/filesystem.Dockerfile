FROM python:3.11-slim

WORKDIR /app

COPY requirements-filesystem.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/proxies/filesystem_main.py /app/main.py

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8080

# Command to run the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
