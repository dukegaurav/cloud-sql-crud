FROM python:3.13.9-slim

SHELL ["/bin/bash", "-c"]

RUN groupadd -g 1001 python && useradd -m -u 1001 -g python python

RUN chown -R python:python /home/python

USER python

WORKDIR /home/python

ENV PATH=/home/python/.local/bin:$PATH

RUN mkdir -p .config/pip

# COPY pip.conf .config/pip/

RUN mkdir app

WORKDIR /home/python/app

COPY pyproject.toml .

RUN pip install --no-cache-dir uv && \
    uv sync

ENV PATH=/home/python/app/.venv/bin:$PATH

COPY ./src .
EXPOSE 5000

# CMD ["cat"]
CMD ["waitress-serve", "--listen=*:5000", "app:app"]

