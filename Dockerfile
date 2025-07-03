FROM python:3.13.0-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add --no-cache ffmpeg gcc musl-dev libffi-dev python3-dev

COPY r.txt ./
RUN pip install --no-cache-dir -r r.txt

COPY . .
