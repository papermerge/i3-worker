FROM python:3.12-slim-bookworm

WORKDIR /app
ENV VIRTUAL_ENV=/app/venv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    imagemagick \
    gcc \
    poppler-utils &&\
    rm -rf /var/lib/apt/lists/*

COPY poetry.lock pyproject.toml README.md LICENSE /app/

RUN pip install --upgrade poetry && \
    python -m venv ${VIRTUAL_ENV} && \
    poetry install -E pgsql -v

COPY i3worker /app/i3worker/

COPY docker/run.bash /run.bash
RUN chmod +x /run.bash

ENTRYPOINT ["/run.bash"]
CMD ["worker"]
