FROM python:3.8-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install --assume-yes gcc libpq-dev vim ffmpeg curl gettext


RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

# COPY . /app/

RUN rm /bin/sh && ln -s /bin/bash /bin/sh
