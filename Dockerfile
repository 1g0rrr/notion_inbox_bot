FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app
COPY .env /app/.env
COPY init_postgres.env /app/init_postgres.env
RUN pip install libs/notion-py