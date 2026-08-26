FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 patchproof \
    && chown -R patchproof:patchproof /app
USER patchproof

CMD ["uvicorn", "packages.api.bootstrap:build_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
