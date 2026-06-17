FROM python:3.12-slim

WORKDIR /app

# get_changed_items() runs git diff against the CI checkout
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .
