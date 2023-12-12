FROM python:3.11-slim

WORKDIR /usr/src/app

COPY . /usr/src/app
COPY requirements.txt ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENV DRIVER_FROM_DOCKER=True
