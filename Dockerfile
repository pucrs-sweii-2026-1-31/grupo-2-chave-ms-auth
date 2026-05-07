# Build stage: install Python dependencies
FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

RUN python -m pip install --upgrade pip && \
    python -m pip install --prefix=/install --no-cache-dir -r requirements.txt

# Runtime stage: copy installed packages and add Gunicorn
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=builder /install /usr/local
COPY . /app

RUN python -m pip install --no-cache-dir gunicorn

EXPOSE 3001
CMD ["gunicorn", "--bind", "0.0.0.0:3001", "run:app"]
