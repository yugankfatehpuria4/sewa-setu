#!/usr/bin/env bash
# Prepare local seed + start the development stack.
# Usage: SEWASETU_ADMIN_PASSWORD=choose-one ./scripts/bootstrap-local.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  : "${SEWASETU_ADMIN_PASSWORD:?Set SEWASETU_ADMIN_PASSWORD or create a .env (must not be sewasetu@123)}"
  cat > .env <<EOF
SEWASETU_ADMIN_USER=${SEWASETU_ADMIN_USER:-assessor}
SEWASETU_ADMIN_PASSWORD=${SEWASETU_ADMIN_PASSWORD}
SEWASETU_PENSION_SCHEME_DEADLINE=${SEWASETU_PENSION_SCHEME_DEADLINE:-2099-12-31 23:59}
EOF
  chmod 600 .env
  echo "Wrote local .env (gitignored)."
fi

if [ ! -f seed/seed.sql ]; then
  cp seed/seed.example.sql seed/seed.sql
  echo "Created seed/seed.sql from seed.example.sql (demo data)."
fi

docker compose --env-file .env up --build -d
echo "Waiting for health..."
for i in $(seq 1 40); do
  if curl -fsS http://localhost:8000/healthz >/dev/null 2>&1; then
    echo "OK  http://localhost:8000/healthz"
    echo "App http://localhost:8000   SMS console http://localhost:8000/__gateway/"
    echo "Admin user: ${SEWASETU_ADMIN_USER:-assessor}"
    exit 0
  fi
  sleep 2
done
echo "Stack started but /healthz not ready yet. Check: docker compose ps && docker compose logs app"
exit 1
