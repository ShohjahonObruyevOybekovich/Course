FROM python:3.11-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \ffmpeg
RUN pip install praat-parselmouth

COPY ./r.txt /usr/src/app/r.txt
RUN pip install -r r.txt

COPY . .
