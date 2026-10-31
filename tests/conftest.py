"""Shared fixtures. Tests run ONLY against the isolated sewasetu_test database
with synthetic data; they never touch citizen data."""
import io
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(ROOT, "app")
UPLOADS = tempfile.mkdtemp(prefix="sewasetu-test-uploads-")

os.environ.setdefault("SEWASETU_DATABASE_HOST", os.environ.get("TEST_DB_HOST", "localhost"))
os.environ.setdefault("SEWASETU_DATABASE_PORT", os.environ.get("TEST_DB_PORT", "5432"))
os.environ["SEWASETU_DATABASE_NAME"] = "sewasetu_test"   # never the production DB
os.environ.setdefault("SEWASETU_DATABASE_USER", "sewasetu")
os.environ.setdefault("SEWASETU_DATABASE_PASSWORD", "sewasetu123")
os.environ["SEWASETU_APP_UPLOAD_DIR"] = UPLOADS
os.environ["SEWASETU_APP_SECRET_KEY"] = "test-only-secret"
os.environ["SEWASETU_PENSION_SCHEME_DEADLINE"] = "2099-12-31 23:59"
os.environ.setdefault("SEWASETU_ADMIN_PASSWORD", "test-admin-password")
sys.path.insert(0, APP_DIR)

import app as appmod  # noqa: E402

assert appmod.cfg("database", "name") == "sewasetu_test"

SCHEMA = open(os.path.join(APP_DIR, "schema.sql")).read()


@pytest.fixture(scope="session", autouse=True)
def _schema():
    conn = appmod.get_db()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS applications, portal_users, otps, decision_audit CASCADE")
    cur.execute(SCHEMA)
    mig = os.path.join(ROOT, "migrations")
    if os.path.isdir(mig):
        for f in sorted(os.listdir(mig)):
            if f.endswith(".up.sql"):
                cur.execute(open(os.path.join(mig, f)).read())
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def clean_db():
    conn = appmod.get_db()
    cur = conn.cursor()
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    tables = [r[0] for r in cur.fetchall()]
    cur.execute("TRUNCATE %s RESTART IDENTITY CASCADE" % ", ".join(tables))
    conn.commit()
    conn.close()
    yield


@pytest.fixture
def sms(monkeypatch):
    sent = []
    monkeypatch.setattr(appmod, "send_sms", lambda m, t: sent.append((m, t)))
    return sent


@pytest.fixture
def client(sms):
    appmod.app.config["TESTING"] = True
    with appmod.app.test_client() as c:
        yield c


def db_one(sql, args=()):
    conn = appmod.get_db()
    cur = conn.cursor()
    cur.execute(sql, args)
    row = cur.fetchone()
    conn.close()
    return row


def db_exec(sql, args=()):
    conn = appmod.get_db()
    cur = conn.cursor()
    cur.execute(sql, args)
    conn.commit()
    conn.close()


TINY_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
TINY_JPG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00" + b"\x00" * 64 + b"\xff\xd9"

DEFAULT_FORM = {
    1: {"applicant_name": "Ramesh Kumar", "dob": "15/08/1950", "gender": "Male",
        "marital_status": "Married", "husband_name": "", "husband_employer": ""},
    2: {"village": "Sonari Gaon", "block": "Sonari"},
    3: {"bank_account": "123456789012", "ifsc": "SBIN0001234"},
}


def verify_mobile(client, mobile):
    client.get("/apply")
    client.post("/apply", data={"mobile": mobile, "captcha": "2"})
    code = db_one("SELECT code FROM otps WHERE mobile=%s ORDER BY id DESC LIMIT 1", (mobile,))[0]
    return client.post("/verify", data={"otp": code})


def fill_form(client, overrides=None):
    overrides = overrides or {}
    for step in (1, 2, 3):
        data = dict(DEFAULT_FORM[step])
        for k in list(overrides):
            if k in data:
                data[k] = overrides[k]
        client.post("/form/%d" % step, data=data)


def upload(client, content=TINY_PDF, filename="age_proof.pdf"):
    return client.post("/upload", data={"document": (io.BytesIO(content), filename)},
                       content_type="multipart/form-data")


def full_apply(client, mobile="9876543210", **overrides):
    verify_mobile(client, mobile)
    fill_form(client, overrides)
    upload(client)
    return client.post("/declaration", data={"agree": "on"})
