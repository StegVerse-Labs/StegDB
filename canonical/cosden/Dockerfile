# Dockerfile for CosDenOS API service

FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy project metadata and install dependencies
COPY pyproject.toml /app/

RUN pip install --upgrade pip \
 && pip install "fastapi>=0.115.0" "uvicorn[standard]>=0.30.0" "pydantic>=2.7.0" \
 && pip install -e .

# Copy source code
COPY src /app/src

# Expose API port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "CosDenOS.api:app", "--host", "0.0.0.0", "--port", "8000"]
