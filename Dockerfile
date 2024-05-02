FROM python:3.11-alpine as main

ENV PYTHONUNBUFFERED=1

ADD uptimealert/ /
ADD .env /.env
ADD requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn
