FROM python:3.14-slim-bookworm

RUN apt-get update && apt-get install -y \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY pyproject.toml /code/pyproject.toml
COPY uv.lock /code/uv.lock

RUN pip install --no-cache-dir uv

RUN uv sync --locked --all-extras --dev

# Self-signed certificate for the HTTPS listener used by the tls_verify acceptance tests.
RUN openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
    -keyout /code/tls-key.pem -out /code/tls-cert.pem \
    -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

COPY ./test_app /code/test_app

EXPOSE 80 8443

# Same app over plain HTTP on port 80 and over HTTPS with the self-signed certificate on port 8443.
CMD ["sh", "-c", "uv run uvicorn test_app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile /code/tls-key.pem --ssl-certfile /code/tls-cert.pem & exec uv run fastapi run /code/test_app/main.py --port 80"]
