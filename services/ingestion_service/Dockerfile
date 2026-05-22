FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
RUN pip install uv && uv pip install --system -r requirements/base.txt
COPY . .
CMD ["uvicorn", "services.ingestion_service.main:app", "--host", "0.0.0.0", "--port", "8001"]