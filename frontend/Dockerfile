# ── MyBagHub Frontend ─────────────────────────────────────────────────────────
# Build from the project root:
#   docker build -f frontend/Dockerfile -t mybagbub-frontend .
#
# Run:
#   docker run -d \
#     --name mybagbub-frontend \
#     -p 8080:8080 \
#     -v /path/to/frontend-config:/config \
#     mybagbub-frontend
#
# The frontend does NOT depend on the backend at startup.
# Users connect to a backend node at runtime via the server-selection page.

FROM docker.1ms.run/python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MY_LIBRARY_FRONTEND_CONFIG_PATH=/config/config.json

COPY frontend/requirements.txt ./
RUN pip3 install --no-cache-dir --retries 5 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r requirements.txt --break-system-packages

COPY frontend/ ./frontend/

RUN mkdir -p /config

VOLUME ["/config"]

EXPOSE 8080

CMD ["python", "-m", "frontend.app"]
