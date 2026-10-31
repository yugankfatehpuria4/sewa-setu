"""F-03: nightly deemed-approval job crashes every night since 2026-03-15
(cron.log: FileNotFoundError /app/config/settings.ini, after CR-2026-031
consolidated config into app.ini). Applications past the 15-day RTPS SLA
are no longer deemed approved."""
import importlib.util
import os
from datetime import datetime, timedelta

import pytest

from conftest import ROOT, db_exec, db_one

SCRIPT = os.path.join(ROOT, "app", "scripts", "deemed_approval.py")


def _load_job():
    spec = importlib.util.spec_from_file_location("deemed_approval_job", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seed(mobile, days_old, status="PENDING"):
    db_exec("INSERT INTO applications (application_no, applicant_name, mobile, dob, status, submitted_at) "
            "VALUES (%s, 'Synthetic Test', %s, '1950-01-01', %s, %s)",
            ("T" + mobile, mobile, status, datetime.now() - timedelta(days=days_old)))


@pytest.mark.xfail(strict=True, reason="F-03")
def test_job_runs_with_consolidated_config(monkeypatch):
    assert not os.path.exists(os.path.join(ROOT, "app", "config", "settings.ini"))
    job = _load_job()
    monkeypatch.setattr(job.requests, "post", lambda *a, **k: None)
    _seed("9600000001", 20)
    _seed("9600000002", 3)
    _seed("9600000003", 40, status="REJECTED")
    job.main()
    assert db_one("SELECT status, decided_by FROM applications WHERE mobile='9600000001'") == ("DEEMED_APPROVED", "RTPS-AUTO")
    assert db_one("SELECT status FROM applications WHERE mobile='9600000002'")[0] == "PENDING"
    assert db_one("SELECT status FROM applications WHERE mobile='9600000003'")[0] == "REJECTED"


@pytest.mark.xfail(strict=True, reason="F-03")
def test_job_is_idempotent(monkeypatch):
    job = _load_job()
    sent = []
    monkeypatch.setattr(job.requests, "post", lambda *a, **k: sent.append(k))
    _seed("9600000004", 16)
    job.main()
    job.main()
    assert len(sent) == 1, "applicant must be notified exactly once"
