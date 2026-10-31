# Architecture

```mermaid
flowchart LR
  C[Citizen / Officer browser] -->|HTTPS| CAD[Caddy]
  CAD --> APP[Flask app · gunicorn]
  APP --> DB[(PostgreSQL)]
  APP -->|/__gateway/ proxy + send| SMS[PurvSMS gateway · internal]
  SCH[Scheduler · cron 02:00 IST] -->|deemed_approval.py| DB
  SCH --> SMS
  BK[Backup · daily pg_dump] --> DB
```

Citizen journey: `/apply` (mobile) → OTP SMS → `/verify` → `/form/1..3` → `/upload` → `/declaration` → confirmation + `/ack/<id>.pdf` → `/status` login → `/application/<id>`.
Officer journey: `/admin` → `/admin/dashboard` → `/admin/applications?status=` → `/admin/application/<id>` → approve/reject.
Nightly: applications `PENDING` beyond 15 days → `DEEMED_APPROVED` + SMS.
