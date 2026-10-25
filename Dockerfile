# =============================================================================
# Astatarote SaaS — image de production
# Build le frontend, le sert via FastAPI (frontend/dist monté par main.py).
# =============================================================================

# ---- Étape 1 : build du frontend ----
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- Étape 2 : runtime ----
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend /build/dist ./frontend/dist

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
