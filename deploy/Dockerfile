# syntax=docker/dockerfile:1
# Local/reviewed artifact only. Do not deploy before blocker closure and approval.
FROM node:24-bookworm-slim AS frontend
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm ci --include=dev --strict-ssl=true
COPY frontend/ ./
# The optional Studio installation is excluded from this build context.
RUN VITE_API_URL='' VITE_ANALYTICS_RENDERER=community npm run build

FROM python:3.12-slim-bookworm
ENV APP_ENV=production PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 OMP_THREAD_LIMIT=1 FRONTEND_DIST=/app/frontend-dist
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng ca-certificates && rm -rf /var/lib/apt/lists/*
COPY backend/requirements-app.txt backend/requirements-payments.txt ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install -r requirements-app.txt && pip check
COPY --chown=0:0 backend/app ./app
COPY --chown=0:0 backend/alembic.ini ./
COPY --chown=0:0 backend/migrations ./migrations
COPY --from=frontend --chown=0:0 /ui/dist ./frontend-dist
RUN useradd --uid 10001 --create-home appuser && chmod -R u=rwX,go=rX /app/app /app/migrations /app/alembic.ini /app/frontend-dist
USER appuser
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','10000')+'/api/health',timeout=2)"
# No migrations, access logs, model downloads or private storage initialization.
CMD ["sh","-c","exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --no-access-log"]
