# Security

Fixed: IDOR on `/application/<id>` and `/ack/<id>.pdf` (F-04); citizen-callable approve/reject (F-04); upload path traversal and type spoofing (F-02); SQL injection in `/status/reset`; hardcoded admin password and committed secret key (now server env; leaked value refused); HttpOnly/SameSite/Secure cookies; security headers and body limit at Caddy.

Remaining risks: status password = DOB; no CSRF tokens; CAPTCHA not verified; no OTP attempt limit or rate limiting; `/__gateway/` publicly lists OTPs (required by the brief); bank accounts unmasked in admin view; no audit table for decisions; the vendor secret key and DB password remain in git history of `config/app.ini` (values are overridden in production and must never be reused).
