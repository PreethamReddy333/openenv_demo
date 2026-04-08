FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source into the compliance_checker package directory
RUN mkdir -p /app/compliance_checker
COPY . /app/compliance_checker/

# Ensure PYTHONPATH includes /app so 'compliance_checker' is importable as a package
ENV PYTHONPATH=/app

# HF Spaces uses port 7860 by default
EXPOSE 7860

CMD ["uvicorn", "compliance_checker.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
