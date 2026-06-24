FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get install -y postgresql-client-common postgresql-client

COPY scripts/startup.sh /startup.sh
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

RUN chmod +x /startup.sh

ENTRYPOINT ["/startup.sh"]
COPY requirements/base.txt requirements/base.txt
RUN pip install uv && uv pip install --system -r requirements/base.txt

COPY . .

CMD ["uvicorn", "services.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
