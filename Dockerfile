FROM python:3.13.0-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


COPY ./r.txt /usr/src/app/r.txt
RUN pip install -r r.txt

COPY . /usr/src/app
