FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/base.txt
RUN pip install uv && uv pip install --system -r requirements/base.txt
RUN pip install streamlit==1.36.0 plotly==5.22.0 pandas==2.2.2

COPY . .

CMD ["streamlit", "run", "frontend/streamlit_app/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]