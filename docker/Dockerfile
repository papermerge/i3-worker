FROM python:3.13-alpine3.22

WORKDIR /app

RUN apk update && apk add linux-headers \
    python3-dev \
    libpq-dev \
    libc-dev \
    imagemagick \
    gcc \
    poppler-utils && \
    # ensure all packages are up-to-date
    apk upgrade --no-cache && \
    rm -rf /var/cache/apk/*

COPY poetry.lock pyproject.toml README.md LICENSE /app/

RUN pip install --upgrade poetry

COPY i3worker /app/i3worker/
RUN poetry install -E pg -v

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
