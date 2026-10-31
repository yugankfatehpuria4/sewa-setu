# Sewa Setu — Old Age Pension Portal (Digital Fellow handover)

Inherited Flask + PostgreSQL portal, repaired rather than rewritten. Live URL: set after running `deploy/deploy.sh` (see `submission` notes).

## Quick start (local)
```
cp seed/seed.example.sql seed/seed.sql   # or the department handout seed
SEWASETU_ADMIN_PASSWORD=choose-one ./scripts/bootstrap-local.sh
# → http://localhost:8000   SMS console → /__gateway/
```
Or manually: `SEWASETU_ADMIN_PASSWORD=choose-one docker compose up --build`.

Production: `docs/DEPLOYMENT.md` (one command to a fresh VPS, HTTPS via Caddy).

## Top five fixes (ranked by citizen impact) — see `docs/FIXES.md`
| # | Fix | Where to see it |
|---|---|---|
| 1 | Final submission no longer fails (40.1% 5xx in logs) | Submit an application; retry with same mobile shows the existing number |
| 2 | Upload accepts JPG/PDF up to 5 MB with clear errors | `/upload` with a phone photo |
| 3 | Deemed-approval job runs again (dead since 15 Mar) | `/admin/applications?status=DEEMED_APPROVED` after 02:00 IST |
| 4 | Citizens see only their own record; only staff approve | `/application/<other id>` → 404; citizen POST `/admin/approve/<id>` → 403 |
| 5 | Names (any Indian script) and DD/MM/YYYY dates stored exactly | Apply with a Hindi name; check the status page |

Git history shows each as a `test:` commit (strict xfail) followed by its `fix:` commit.

## Docs
`docs/INVESTIGATION.md` · `docs/FIXES.md` · `docs/DECISIONS.md` · `docs/SECURITY.md` · `docs/TESTING.md` · `docs/DEPLOYMENT.md` · `docs/ARCHITECTURE.md` · `docs/LOOM_SCRIPT.md` · `docs/evidence/` · log analysis `analysis/analyze_logs.py`

## Admin access
The admin password is set only via env (`SEWASETU_ADMIN_PASSWORD` locally, or `ADMIN_PASSWORD` in the server `.env`); the vendor's hardcoded password is refused.
