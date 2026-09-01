FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates gnupg lsb-release python3 python3-pip python3-venv && \
    curl -1sLf 'https://dl.cloudsmith.io/public/wand/libwandio/cfg/setup/bash.deb.sh' | bash && \
    curl -fsSL https://pkg.caida.org/os/ubuntu/keyring.gpg -o /etc/apt/trusted.gpg.d/caida.gpg && \
    echo "deb https://pkg.caida.org/os/ubuntu noble main" > /etc/apt/sources.list.d/caida.list && \
    apt-get update && apt-get install -y --no-install-recommends bgpstream && \
    useradd --create-home --uid 10001 appuser && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser app ./app

ENV PATH="/opt/venv/bin:$PATH"
USER appuser
EXPOSE 17991
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:17991/api/health || exit 1
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","17991","--proxy-headers"]
