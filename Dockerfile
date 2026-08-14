# ==============================================================================
# Dockerfile — MyTodos FastAPI app (Alpine)
# ------------------------------------------------------------------------------
# Base image: uv's official Python 3.13 Alpine image. Python 3.13.15 in the
# image matches the local version (3.13.1, see .python-version), so the bytecode
# and runtime behaviour are identical. Alpine = tiny (~50 MB) final image.
# ==============================================================================
# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder

# --- Builder stage: install ONLY the locked dependencies ----------------------
# - UV_COMPILE_BYTECODE=1: precompile .pyc files (faster cold start)
# - UV_LINK_MODE=copy: copy packages into the venv instead of hard-linking
#   (hard links break across Docker layer boundaries)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Alpine (musl) wheels exist for the big C deps (bcrypt, cryptography,
# psycopg, pydantic-core), but a few packages in uv.lock only ship as
# source archives (sdists). Install build tools so `uv sync` can compile
# them from source if a wheel is missing. These tools live ONLY in this
# builder stage — they never reach the final image.
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev linux-headers

# Working directory for the whole build
WORKDIR /app

# Install dependencies from the lockfile only (--frozen = fail if uv.lock is
# out of date). --no-dev skips the dev/test tools. --no-install-project keeps
# our source code out of this layer so dep installs stay cached.
#
# --mount=type=cache: cache uv's download/compile cache in BuildKit so rebuilds
#   are fast. --mount=type=bind: read pyproject.toml + uv.lock without copying
#   them into the layer.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# ==============================================================================
# Final (runtime) stage: minimal Alpine image with venv + source code only
# ==============================================================================
FROM ghcr.io/astral-sh/uv:python3.13-alpine

# Run as a non-root user (security best practice).
# NOTE: the Alpine variant of this image ships NO built-in user, so we create
# one explicitly (uid 1000, group "app", no password, no home dir).
RUN addgroup -S app && adduser -D -H -G app -u 1000 app

USER app

WORKDIR /app

# Copy the pre-built virtualenv from the builder stage.
# .venv/bin is prepended to PATH so `uvicorn` resolves to the venv binary.
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy application source code.
# NOTE: .env is intentionally NOT copied — secrets must be passed at runtime
# via environment variables (pydantic-settings gives env vars precedence over
# the .env file), e.g.:
#   docker run -e DATABASE_URL=... -e SECRET_KEY=... -p 8000:8000 mytodos
COPY --chown=app:app app ./app
COPY --chown=app:app router ./router

# Alembic files so DB migrations can be run inside the container:
#   docker exec <container> /app/.venv/bin/alembic upgrade head
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./alembic.ini

# Expose the port uvicorn listens on
EXPOSE 8000

# Health check: busybox wget (bundled with Alpine) hits the app root.
# The app requires a valid JWT for GET /, so a 401 still proves the server is up.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:8000/docs || exit 1

# Run the FastAPI app with uvicorn (the FastAPI standard install provides it).
# NOTE: the app creates tables on startup (Base.metadata.create_all in
# app/main.py), so the database must be reachable before starting the container.
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]