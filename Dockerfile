FROM python:3.12-slim-bookworm

WORKDIR /app

# ============================================================
# Systempakete
# ============================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Docker Official Repository
# ============================================================

RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg \
       -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo \
       "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" \
       > /etc/apt/sources.list.d/docker.list

# ============================================================
# Docker CLI + Compose Plugin
#
# KEIN Docker Engine / KEIN Docker Daemon!
# ============================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        docker-ce-cli \
        docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Python-Abhängigkeiten
# ============================================================

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Album Manager
#
# app.py und Python-Dateien
# ============================================================

COPY src/ /app/

# ============================================================
# Templates
#
# Flask erwartet:
#
# /app/templates/
#
# Die Templates liegen im Projekt unter:
#
# src/templates/
# ============================================================

COPY src/templates/ /app/templates/

# ============================================================
# Start
# ============================================================

CMD ["python", "app.py"]
