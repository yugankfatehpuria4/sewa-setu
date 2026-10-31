# Investigation — Sewa Setu Old Age Pension Portal

All log numbers come from `python -I analysis/analyze_logs.py <extracted-logs>`; full output in
`docs/evidence/log-analysis-output.txt`. Period 01 Jan – 30 Jun 2026, 1,515,987 HTTP requests.

## What could and could not be checked

| Source | Status |
|---|---|
| Code, templates, config, SMS gateway | Read in full |
| Logs (nginx, app, cron) | Analysed with reproducible script |
| `seed/seed.sql` (citizen data) | **NOT CHECKED — the file was not in the handout I received.** All data-level claims are UNVERIFIED. |
| `dc-briefing.mp3` | **NOT TRANSCRIBED — every speech-model host (Hugging Face, OpenAI, GitHub releases) is blocked from my build sandbox.** No complaint below is attributed to the DC. Run `scripts/transcribe_briefing.sh` and map items to findings before recording the Loom. |

## Key numbers

| Metric | Value |
|---|---|
| Final submissions (`POST /declaration`) | 34,332 — **13,759 failed (40.1%)**: 6,886 × 500, 6,873 × 504 |
| Submission latency | p50 13.1 s, p95 30.0 s (= gunicorn timeout) |
| App errors "too many clients already" | 13,759 (one per failed submission) |
| Upload step | 75,815 `POST /upload`; only 34,332 reached the declaration page |
| Deemed-approval job | 73 good runs to 14 Mar (2,248 approvals, ~30.8/night); **crashed every night 15 Mar – 30 Jun (108 nights)** |
| Status page `GET /application/<id>` | p50 3.15 s, p95 7.52 s |
| Footer links `/rti`, `/grievance`, `/contact`, `/downloads/*` | ~4,800 × 404 each — citizens looking for help hit dead links |
| Peak traffic | 11 req/s (28 May 18:32); busiest days are month-ends (30 Jan: 80,131 requests) |
| SMS gateway timeouts | 62 |
| Attack patterns (enumeration, injection, admin hits) | None observed in logs |

## Findings

### F-01: Two in five final submissions fail
- Status: CONFIRMED · Category: Citizen Journey / Performance
- Evidence: logs — 13,759/34,332 `POST /declaration` 5xx; app log pairs each with `psycopg2.OperationalError: too many clients already` during "generating acknowledgment pdf". Code — `handle_submission` keeps its DB connection open while `generate_acknowledgment` draws 4,000 line segments; exceptions skip `conn.close()` (leak). The row is committed *before* the PDF, so the citizen sees an error, retries, and gets "Duplicate applications are not permitted" — a dead end.
- Citizens affected: 13,759 failed attempts in six months.
- Severity: Critical — blocks the service at the last step and tells saved applicants they failed.

### F-02: Upload rejects what the page asks for
- Status: CONFIRMED (code + reproduction); funnel loss from logs
- Evidence: `upload.html` says "JPG or PDF, maximum 5 MB"; `app.py` accepts only `.pdf` ≤ 102,400 bytes and replies `ERR_VAL_47`. Reproduced by `tests/test_fix02_upload.py`. Client filename used in path → `../` crashes (path traversal). Logs: 75,815 uploads attempted vs 34,332 reaching declaration. Note: every logged `POST /upload` is 200 (a success would be 302), so the per-request split is UNVERIFIED; the funnel loss is not.
- Severity: Critical — phone photos (JPG, 1–4 MB) are the normal way elderly citizens provide age proof.

### F-03: Deemed approval (RTPS Act) stopped on 15 March
- Status: CONFIRMED
- Evidence: `cron.log` — `FileNotFoundError: /app/config/settings.ini` every night from 15 Mar; config was consolidated into `app.ini` (CR-2026-031) but `scripts/deemed_approval.py` was not updated.
- Citizens affected: UNVERIFIED (needs seed); at the Jan–Mar rate, ~3,300 applications (108 × 30.8) should have been deemed approved and were not.
- Severity: Critical — a statutory entitlement silently withheld.

### F-04: Any citizen can read any record and approve applications
- Status: CONFIRMED (reproduction)
- Evidence: `/application/<id>` checks only `logged_in`; `/ack/<id>.pdf` has no check (name, DOB, bank account, IFSC for every id). `/admin/approve|reject` check `session["logged_in"]`, which citizen login sets. Reproduced in `tests/test_fix04_authorisation.py`. No exploitation seen in logs.
- Severity: Critical — ~100,000 citizens' bank details exposed; pension fraud possible.

### F-05: Names and dates of birth stored wrongly
- Status: CONFIRMED (reproduction); historical extent UNVERIFIED (needs seed)
- Evidence: `sanitize()` cuts names to 20 UTF-8 **bytes** — "रामेश्वर प्रसाद त्रिपाठी" keeps ~6 characters; long English names cut too. DOB parsed `%m/%d/%Y` first though the form asks DD/MM/YYYY: 05/03/1960 → 3 May 1960, which also changes the DOB-based status password and the age check.
- Severity: High — the record of who the citizen is, used for disbursement and identity checks.

### Other findings (not in top five)
- F-06 SQL injection in `/status/reset` (string-formatted SQL) — fixed in hardening commit.
- F-07 Hardcoded admin password `sewasetu@123` and committed secret key — moved to server env; leaked value refused.
- F-08 Status password = DOB (guessable); reset sets it back to DOB — recommended, not implemented (needs dept. decision on citizen login).
- F-09 `/__gateway/` exposes every OTP publicly — required by the brief for assessment; documented risk.
- F-10 No CSRF tokens; CAPTCHA answer never checked; OTP has no attempt limit — recommended.
- F-11 Footer links 404 (~4,800 each) — content task for the department.
- F-12 Slow status page — index migration `migrations/001_indexes.up.sql` added; cause UNVERIFIED without seed.
- F-13 Application numbers are random 6 digits with no uniqueness constraint — collision risk grows with volume; recommended unique index after checking seed for existing duplicates.
