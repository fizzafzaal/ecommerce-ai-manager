# syntax=docker/dockerfile:1
#
# Builds ShopSphere as a single container for Railway (or any Docker host):
#   Stage 1 compiles the React storefront into static files.
#   Stage 2 installs the Python backend + Tesseract, copies in those static
#           files, seeds the database + search index, and runs the API which
#           also serves the frontend.

# ---------- Stage 1: build the React storefront ----------
FROM node:20-slim AS frontend
WORKDIR /app/storefront

# Install dependencies first so this layer caches unless package files change.
COPY storefront/package*.json ./
RUN npm install

# Build the production bundle -> /app/storefront/dist
COPY storefront/ ./
RUN npm run build


# ---------- Stage 2: the Python backend (also serves the built frontend) ----------
FROM python:3.11-slim

# Tesseract is the OCR engine used to verify uploaded invoice images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only PyTorch first. The default torch wheel is the multi-GB CUDA
# build; we have no GPU in the cloud, so the CPU wheel keeps the image small.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Then the rest of the Python dependencies (sentence-transformers reuses the
# torch already installed above).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend source code.
COPY app/ ./app/

# Built frontend from stage 1.
COPY --from=frontend /app/storefront/dist ./storefront/dist

# Seed the database and build the product search index at build time, so the
# container boots fast and is self-contained. (This baked-in data resets on
# each redeploy -- fine for a demo; swap to a managed DB for persistence.)
RUN python -m app.seed && python -m app.vector_store

# Railway sets $PORT at runtime; default to 8000 for a local `docker run`.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
