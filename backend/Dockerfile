FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml
COPY pyproject.toml .

# Install dependencies using pip
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "msgspec>=0.19.0" \
    "tortoise-orm>=0.22.0" \
    "aiosqlite>=0.20.0" \
    "ollama>=0.4.0" \
    "python-docx>=1.1.0" \
    "openpyxl>=3.1.0" \
    "python-pptx>=1.0.0" \
    "PyMuPDF>=1.25.0" \
    "Pillow>=10.0.0" \
    "psutil>=5.9.0" \
    "loguru>=0.7.0" \
    "python-multipart>=0.0.9" \
    "sse-starlette>=2.0.0" \
    "tzdata"

# Copy application code
COPY app/ app/

# Create data directories
RUN mkdir -p data/uploads data/outputs data/knowledge

ENV PYTHONUNBUFFERED=1
ENV KAVACH_HOST=0.0.0.0
ENV KAVACH_PORT=8000
ENV OLLAMA_HOST=http://host.docker.internal:11434

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
