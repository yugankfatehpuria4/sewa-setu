"""F-01: final submission fails (40.1% 5xx on POST /declaration in prod logs)."""
import pytest
from fpdf import FPDF

from conftest import appmod, db_one, full_apply


def test_submission_succeeds_even_if_ack_pdf_fails(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("simulated: too many clients already")
    monkeypatch.setattr(appmod, "generate_acknowledgment", boom)
    r = full_apply(client, mobile="9811111111")
    assert r.status_code == 200
    assert b"Application Submitted" in r.data
    assert db_one("SELECT count(*) FROM applications WHERE mobile='9811111111'")[0] == 1


def test_ack_pdf_border_is_cheap(client, monkeypatch):
    full_apply(client, mobile="9822222222")
    app_id = db_one("SELECT id FROM applications WHERE mobile='9822222222'")[0]
    calls = []
    orig = FPDF.line

    def counting(self, *a, **k):
        calls.append(1)
        return orig(self, *a, **k)
    monkeypatch.setattr(FPDF, "line", counting)
    import os
    p = os.path.join(appmod.UPLOAD_DIR, "ack", "%d.pdf" % app_id)
    if os.path.exists(p):
        os.remove(p)
    r = client.get("/ack/%d.pdf" % app_id)
    assert r.status_code == 200 and r.data.startswith(b"%PDF")
    assert len(calls) <= 10, "ack PDF draws %d line segments" % len(calls)


def test_retry_after_failed_submission_shows_existing_application(client, monkeypatch):
    """A citizen whose submission errored (row saved) and who retries must be
    shown their application number, not a dead-end 'duplicate' error."""
    full_apply(client, mobile="9833333333")
    app_no = db_one("SELECT application_no FROM applications WHERE mobile='9833333333'")[0]
    r = full_apply(client, mobile="9833333333")
    assert app_no.encode() in r.data
