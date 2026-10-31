# Decisions

## D-01 Scheme deadline (needs a department decision)
`config/app.ini` sets `scheme_deadline = 2026-10-31 23:59`. After that, `/apply` closes. The brief expects an assessor to submit applications for ~30 days after submission. Changing a statutory deadline is policy, not engineering, so I did **not** change the default. The deadline can be set from the server env (`SCHEME_DEADLINE` in `.env`) without a code change. Whoever owns the decision should set it.

## D-02 Missing inputs
`seed/seed.sql` was not in the handout I received, and the DC briefing could not be transcribed in the build sandbox (speech-model hosts blocked). Data-level findings are marked UNVERIFIED; nothing is attributed to the DC.

## D-03 Deemed-approval backlog
Fixing F-03 means the next 02:00 run approves every application pending beyond 15 days, including those missed since 15 March. This follows the RTPS Act as written. I did not add a manual gate, because withholding statutory approvals is itself a policy change.

## D-04 Existing citizen records left unchanged
No historical row was edited. Corrupted names/DOBs cannot be reconstructed with certainty (see FIXES §5).

## D-05 Gateway console stays public
`/__gateway/` shows every OTP to anyone. The brief requires it for the assessor. In a real deployment it must be removed.

## D-06 Baseline test adjusted in F-01
`test_duplicate_application_blocked` asserted the old dead-end redirect. F-01 deliberately replaces it with showing the existing application; the test still asserts no second row is created.

## Deliberately left alone
Eligibility, SLA duration and deemed-approval rules; deleting/rewriting historical applications; replacing Flask/Postgres/server-rendered pages; SPA or microservices; the DOB-as-password scheme (citizen-login redesign needs a department decision); UI redesign (no reliability gain within the time available).

## Build notes
- An edit script opened a test file for writing before reading it and emptied it; caught by the test count (10 instead of 16) and restored before the fix commit.
- The first F-04 fix let the "just submitted" session view full records, not only the acknowledgment; caught by the regression test and narrowed.
