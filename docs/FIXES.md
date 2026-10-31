# Top five fixes, ranked by citizen impact

Scoring (1–5; weights: citizens affected ×3, severity ×3, unauthorised access/data loss ×2, blocks essential service ×2, feasibility ×1).

| Rank | Fix | Affected | Severity | Access/loss | Blocks service | Feasible | Score |
|---|---|---|---|---|---|---|---|
| 1 | F-01 Submission failures | 5 | 5 | 3 | 5 | 5 | **55** |
| 2 | F-02 Upload rejects JPG/>100 KB | 5 | 5 | 2 | 5 | 5 | **53** |
| 3 | F-03 Deemed approval stopped | 4 | 5 | 2 | 4 | 5 | **48** |
| 4 | F-04 IDOR + citizen approvals | 4 | 4 | 5 | 1 | 5 | **41** |
| 5 | F-05 Names/DOB corrupted | 3 | 4 | 4 | 2 | 5 | **40** |

Each fix has a `test:` commit (tests marked `xfail(strict=True)`, proving they fail on the old code) followed by a `fix:` commit removing the markers. Before/after output: `docs/evidence/fix-0N-before.txt` / `-after.txt`.

## 1. F-01 — Final submission fails for two in five applicants
- **Problem:** after the citizen clicks Submit, the server holds a database connection while drawing a needlessly heavy PDF; at busy times Postgres runs out of connections and the page errors — even though the application was already saved. Retrying then said "duplicate not permitted".
- **Change:** close the connection right after commit; generate the acknowledgment with a short-lived connection inside try/except (failure is logged, PDF regenerated on demand at `/ack/<id>.pdf`); border drawn with 2 lines instead of 4,000; a retry now shows the existing application number. Gunicorn moved to threaded workers with a 60 s timeout.
- **Tests:** `tests/test_fix01_submission.py` (3).
- **Alternatives rejected:** async PDF queue (new infra); raising `max_connections` alone (hides the leak).
- **Residual risk:** load not yet measured against the live stack.

## 2. F-02 — Upload rejects the documents citizens have
- **Change:** accept `.pdf/.jpg/.jpeg` up to 5 MB (as the page always said), check file signatures, server-generated filenames (closes path traversal), plain-language errors instead of `ERR_VAL_47`, friendly 413 page.
- **Tests:** `tests/test_fix02_upload.py` (6).
- **Residual risk:** no malware scanning.

## 3. F-03 — Deemed approval stopped on 15 March
- **Change:** job reads `config/app.ini` (legacy `settings.ini` still honoured), env overrides like the web app, and exits loudly if no config. Production scheduler exports env to cron and runs in IST. The SLA rule itself is untouched.
- **Tests:** `tests/test_fix03_deemed_approval.py` (runs with consolidated config; idempotent, one SMS per applicant).
- **Note:** the first run after deployment will deem-approve every application pending >15 days, including the March–June backlog. That is what the law requires, but the DC should know it is coming (see DECISIONS D-03).

## 4. F-04 — Anyone could read records; citizens could approve applications
- **Change:** a citizen sees only applications filed from their own mobile; the acknowledgment is available to its owner, to staff, or to the session that just submitted it; approve/reject require the staff session.
- **Tests:** `tests/test_fix04_authorisation.py` (5, including "admin can still approve").

## 5. F-05 — Names and dates of birth stored wrongly
- **Change:** names normalised (NFC, whitespace) and limited by characters to the column width, never by bytes; DOB accepted only day-first (`/`, `-`, `.` separators).
- **Tests:** `tests/test_fix05_identity_integrity.py` — Hindi, Bengali, Tamil (combining marks) and a long English name round-trip; 05/03/1960 stored as 5 March; status login with the DOB the citizen typed.
- **Existing records:** not altered. Truncated names are not recoverable from the database; swapped DOBs are ambiguous. Recommended: flag rows (`length(applicant_name)` at the byte limit; DOB day ≤ 12) for verification against the uploaded age proof at the block office.
