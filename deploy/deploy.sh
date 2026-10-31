#!/usr/bin/env bash
# One-command deploy to a fresh Ubuntu 22.04/24.04 VPS.
# Usage: VPS_HOST=1.2.3.4 VPS_USER=ubuntu VPS_SSH_KEY_PATH=~/.ssh/id_ed25519 \
#        SEED=/path/to/seed.sql ./deploy/deploy.sh
set -euo pipefail
: "${VPS_HOST:?}" "${VPS_USER:?}" "${VPS_SSH_KEY_PATH:?}" "${SEED:?path to seed/seed.sql}"
DOMAIN="${DOMAIN:-${VPS_HOST}.sslip.io}"
SSH="ssh -i $VPS_SSH_KEY_PATH -o StrictHostKeyChecking=accept-new $VPS_USER@$VPS_HOST"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

$SSH 'set -e; command -v docker >/dev/null || (curl -fsSL https://get.docker.com | sudo sh);
  sudo usermod -aG docker $USER || true;
  sudo apt-get install -y ufw unattended-upgrades >/dev/null;
  sudo ufw allow 22/tcp; sudo ufw allow 80/tcp; sudo ufw allow 443/tcp; sudo ufw --force enable;
  sudo mkdir -p /opt/sewa-setu/seed && sudo chown -R $USER /opt/sewa-setu'

rsync -az --delete -e "ssh -i $VPS_SSH_KEY_PATH" --exclude .git --exclude seed \
  --exclude submission --exclude '.env*' "$ROOT/" "$VPS_USER@$VPS_HOST:/opt/sewa-setu/"
rsync -az -e "ssh -i $VPS_SSH_KEY_PATH" "$SEED" "$VPS_USER@$VPS_HOST:/opt/sewa-setu/seed/seed.sql"

$SSH "cd /opt/sewa-setu && if [ ! -f .env ]; then
  ADMINPW=\$(openssl rand -base64 18 | tr -d '/+=');
  printf 'DOMAIN=%s\nDB_PASSWORD=%s\nSECRET_KEY=%s\nADMIN_USER=assessor\nADMIN_PASSWORD=%s\n' \
    '$DOMAIN' \$(openssl rand -hex 24) \$(openssl rand -hex 32) \$ADMINPW > .env; chmod 600 .env;
  echo \"ADMIN PASSWORD (save it now): \$ADMINPW\"; fi
  sudo docker compose -f docker-compose.prod.yml --env-file .env up -d --build
  sleep 20; sudo docker compose -f docker-compose.prod.yml ps"
echo "Verify:  curl -fsS https://$DOMAIN/healthz"
