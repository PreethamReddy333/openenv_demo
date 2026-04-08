FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Ensure PYTHONPATH includes /app so imports work
ENV PYTHONPATH=/app

# HF Spaces uses port 7860
EXPOSE 7860

CMD ["uvicorn", "compliance_checker.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
