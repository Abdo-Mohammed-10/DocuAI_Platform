FROM python:3.11-slim

WORKDIR /app

COPY requirements/base.txt requirements/base.txt

RUN pip install uv && uv pip install --system -r requirements/base.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]