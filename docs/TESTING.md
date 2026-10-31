# Testing

Run: `createdb sewasetu_test` (user `sewasetu`), then `pip install -r app/requirements.txt pytest && pytest -q`.
Tests use only the isolated `sewasetu_test` database with synthetic data (asserted in `tests/conftest.py`).

| Suite | Tests |
|---|---|
| `test_baseline.py` — routes preserved, pages render, full journey, OTP, duplicates | 7 |
| `test_fix01_submission.py` | 3 |
| `test_fix02_upload.py` | 6 |
| `test_fix03_deemed_approval.py` | 2 |
| `test_fix04_authorisation.py` | 5 |
| `test_fix05_identity_integrity.py` | 7 |
| `test_hardening.py` — leaked admin password, SQLi on reset, `/healthz`, HttpOnly | 4 |

Final run: **34 passed** (`docs/evidence/final-test-run.txt`). CI: `.github/workflows/ci.yml`.

## Known gaps (not done in this run)
- Load test (Locust at 2× the measured 11 req/s peak) — not run.
- Accessibility audit (axe/pa11y) — not run; no UI redesign was made.
- Docker stack not built in the build sandbox; first build happens on the VPS.
- Concurrency test for application-number uniqueness — not written (F-13).
