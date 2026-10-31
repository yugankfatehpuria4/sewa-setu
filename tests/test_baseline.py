"""Baseline characterisation of the inherited system (behaviour as received)."""
from conftest import appmod, db_one, full_apply

EXPECTED_ROUTES = {
    "/", "/about", "/__gateway/", "/__gateway/<path:subpath>", "/apply", "/verify",
    "/form/<int:step>", "/upload", "/declaration", "/status", "/application/<int:app_id>",
    "/ack/<int:app_id>.pdf", "/status/reset", "/admin", "/admin/dashboard",
    "/admin/applications", "/admin/application/<int:app_id>",
    "/admin/approve/<int:app_id>", "/admin/reject/<int:app_id>",
}


def test_route_inventory_preserved():
    rules = {r.rule for r in appmod.app.url_map.iter_rules() if r.endpoint != "static"}
    missing = EXPECTED_ROUTES - rules
    assert not missing, "routes removed: %s" % missing


def test_public_pages_render(client):
    for path in ("/", "/about", "/apply", "/status", "/status/reset", "/admin"):
        assert client.get(path).status_code == 200, path


def test_full_citizen_journey_english_name(client, sms):
    r = full_apply(client)
    assert r.status_code == 200
    assert b"Application Submitted" in r.data
    row = db_one("SELECT applicant_name, status FROM applications WHERE mobile='9876543210'")
    assert row == ("Ramesh Kumar", "PENDING")


def test_otp_wrong_code_rejected(client):
    client.get("/apply")
    client.post("/apply", data={"mobile": "9000000001", "captcha": "2"})
    r = client.post("/verify", data={"otp": "000000x"})
    assert b"Invalid OTP" in r.data


def test_form_requires_verified_mobile(client):
    r = client.get("/form/1")
    assert r.status_code == 302 and "/apply" in r.headers["Location"]


def test_duplicate_application_blocked(client):
    full_apply(client, mobile="9876500000")
    full_apply(client, mobile="9876500000")
    # F-01 changed the response from a dead-end redirect to showing the
    # existing application; the second row must still never be created.
    assert db_one("SELECT count(*) FROM applications WHERE mobile='9876500000'")[0] == 1


def test_admin_dashboard_requires_login(client):
    r = client.get("/admin/dashboard")
    assert r.status_code == 302
