FROM python:3.12-slim

# Pinned client library. Used by device, controller and attacker.
RUN pip install --no-cache-dir paho-mqtt==2.1.0

WORKDIR /app
COPY . /app
