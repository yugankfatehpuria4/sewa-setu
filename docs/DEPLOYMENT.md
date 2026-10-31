# Deployment

## Fresh VPS (Ubuntu 22.04/24.04), one command
```
VPS_HOST=<ip> VPS_USER=ubuntu VPS_SSH_KEY_PATH=~/.ssh/id_ed25519 SEED=/path/to/seed/seed.sql ./deploy/deploy.sh
```
Installs Docker, opens only 22/80/443 (UFW), copies the code and seed, writes a server-only `.env`
with random secrets (prints the admin password once), and starts the stack. HTTPS via Caddy on
`<ip>.sslip.io` unless `DOMAIN` is set. The seed loads once, on first start of an empty volume.

For a dry-run without the department handout, use the synthetic demo seed:
`SEED=./seed/seed.example.sql`.

## Services (`docker-compose.prod.yml`)
`db` (Postgres 15, IST, healthcheck) · `app` (gunicorn gthread 4×4, `/healthz` healthcheck) · `scheduler` (cron 02:00 IST, deemed approval) · `smsgw` (internal only; reached through the app at `/__gateway/`) · `caddy` (80/443, auto TLS) · `backup` (daily `pg_dump -Fc`, 14-day retention). All `restart: unless-stopped`, logs rotated.

## Apply the index migration (after a backup)
```
docker compose -f docker-compose.prod.yml exec backup sh -c 'pg_dump -Fc -h db -U sewasetu sewasetu > /backups/pre-001.dump'
docker compose -f docker-compose.prod.yml exec -T db psql -U sewasetu sewasetu < migrations/001_indexes.up.sql
```

## Restore drill
```
docker compose -f docker-compose.prod.yml exec db createdb -U sewasetu restore_test
docker compose -f docker-compose.prod.yml exec backup sh -c 'pg_restore -h db -U sewasetu -d restore_test $(ls -t /backups/*.dump | head -1)'
```

## Verify
`curl -fsS https://<domain>/healthz` → `{"db":"ok","status":"ok"}` · `ss -tlnp` on the host shows only 22/80/443.
Enable a free uptime check (e.g. UptimeRobot, HTTPS monitor on `/healthz`, 5-minute interval).
