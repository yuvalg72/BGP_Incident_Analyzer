# SPDX-License-Identifier: Apache-2.0
FROM caida/bgpstream:2.3.0@sha256:d808116911c107926451f882295d85c80940285791ff38c7e6999976d355e3d4

LABEL org.opencontainers.image.title="BGP Incident Analyzer" \
      org.opencontainers.image.description="Self-hosted BGP incident analysis using CAIDA BGPStream" \
      org.opencontainers.image.source="https://github.com/yuvalg72/BGP_Incident_Analyzer" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl passwd python3-pip python3-venv && \
    useradd --create-home --uid 10001 appuser && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser app ./app
COPY LICENSE NOTICE THIRD_PARTY_NOTICES.md /usr/share/licenses/bgp-incident-analyzer/
COPY LICENSES /usr/share/licenses/bgp-incident-analyzer/LICENSES

ENV PATH="/opt/venv/bin:$PATH"
USER appuser
EXPOSE 17991
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD curl -fsS http://127.0.0.1:17991/api/ready || exit 1
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","17991","--proxy-headers","--no-server-header"]
