"""Deployment-security hardening outside the top five (each trivial/low-risk)."""
from conftest import appmod, db_one, full_apply


def test_leaked_default_admin_password_rejected(client):
    r = client.post("/admin", data={"username": "admin", "password": "sewasetu@123"})
    assert r.status_code == 200 and b"Invalid credentials" in r.data
    with client.session_transaction() as s:
        assert not s.get("admin")


def test_reset_password_not_sql_injectable(client):
    full_apply(client, mobile="9300000001")
    before = db_one("SELECT password_hash FROM portal_users WHERE mobile='9300000001'")[0]
    r = client.post("/status/reset", data={"mobile": "' OR '1'='1"})
    assert r.status_code == 200
    r = client.post("/status/reset", data={"mobile": "x'; UPDATE portal_users SET password_hash='pwned'; --"})
    assert r.status_code == 200
    assert db_one("SELECT password_hash FROM portal_users WHERE mobile='9300000001'")[0] == before


def test_health_endpoint(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.get_json()["db"] == "ok"


def test_session_cookie_httponly(client):
    client.get("/apply")
    cookie = [h for h in client.application.test_client().get("/apply").headers.getlist("Set-Cookie")]
    assert all("HttpOnly" in c for c in cookie)
