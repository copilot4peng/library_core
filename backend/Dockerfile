# ── MyBagHub Backend ──────────────────────────────────────────────────────────
# Build from the project root:
#   docker build -f backend/Dockerfile -t mybagbub-backend .
#
# Run:
#   docker run -d \
#     --name mybagbub-backend \
#     -p 8000:8000 \
#     -v /path/to/config:/config \
#     -v /path/to/data:/data \
#     mybagbub-backend

FROM docker.1ms.run/python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MY_LIBRARY_CONFIG_PATH=/config/config.json

COPY backend/requirements.txt ./
RUN pip3 install --no-cache-dir --retries 5 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r requirements.txt --break-system-packages

COPY backend/ ./backend/

RUN mkdir -p /config /data

VOLUME ["/config", "/data"]

EXPOSE 8000

CMD ["python", "-m", "backend.main"]
