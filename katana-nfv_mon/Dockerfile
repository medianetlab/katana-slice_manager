FROM python:3.7.4-slim

RUN mkdir -p /prom_exporter

WORKDIR /prom_exporter
COPY . .

RUN pip install -r requirements.txt