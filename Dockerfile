FROM docker.1ms.run/python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	MY_LIBRARY_CONFIG_PATH=/config/config.json

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages   

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY run_services.py ./
COPY config.json ./config.json

RUN mkdir -p /config /data

VOLUME ["/config", "/data"]

EXPOSE 8000 8080

CMD ["python", "run_services.py"]
