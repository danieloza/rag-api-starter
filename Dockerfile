FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
COPY docs ./docs
COPY .env.example ./.env.example
COPY LICENSE ./LICENSE
COPY CHANGELOG.md ./CHANGELOG.md
COPY README.md ./README.md

RUN mkdir -p /app/data

EXPOSE 8010

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
