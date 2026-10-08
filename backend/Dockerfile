# syntax=docker/dockerfile:1

# ---- base: shared runtime layer --------------------------------------------
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/venv/bin:$PATH"
RUN groupadd --system --gid 1000 app \
 && useradd --system --uid 1000 --gid app --home-dir /app --no-create-home app
WORKDIR /app

# ---- builder: runtime dependencies in a venv -------------------------------
FROM base AS builder
RUN python -m venv /venv
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- dev-builder: + test and lint tooling ----------------------------------
FROM builder AS dev-builder
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# ---- dev: code is bind-mounted by docker-compose.yml -----------------------
FROM base AS dev
# gettext: makemessages/compilemessages for the Russian admin translation.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gettext \
 && rm -rf /var/lib/apt/lists/*
COPY --from=dev-builder /venv /venv
COPY --chown=app:app . .
USER app
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---- prod: code baked into the image, served by Gunicorn -------------------
FROM base AS prod
COPY --from=builder /venv /venv
COPY --chown=app:app . .
RUN install -d -o app -g app /app/staticfiles
USER app
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
