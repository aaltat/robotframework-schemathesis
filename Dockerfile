FROM python:3.14-slim-bookworm

RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY pyproject.toml /code/pyproject.toml
COPY uv.lock /code/uv.lock

RUN pip install --no-cache-dir uv

RUN uv sync --locked --all-extras --dev

COPY ./test_app /code/test_app

CMD ["uv", "run", "fastapi", "run", "/code/test_app/main.py", "--port", "80"]
