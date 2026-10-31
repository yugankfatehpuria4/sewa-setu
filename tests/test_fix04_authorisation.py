"""F-04: broken authorisation.
 - /application/<id> and /ack/<id>.pdf return ANY citizen's record (name, DOB,
   bank account, IFSC) to any logged-in citizen / anyone (IDOR).
 - /admin/approve and /admin/reject check only session['logged_in'], which the
   citizen status login also sets: a citizen can approve their own pension."""
import pytest

from conftest import appmod, db_one, full_apply


def _two_citizens(client):
    full_apply(client, mobile="9500000001")
    full_apply(client, mobile="9500000002")
    a = db_one("SELECT id FROM applications WHERE mobile='9500000001'")[0]
    b = db_one("SELECT id FROM applications WHERE mobile='9500000002'")[0]
    return a, b


def _citizen_login(client, mobile):
    client.get("/status")
    return client.post("/status", data={"mobile": mobile, "password": "15081950"})


def test_citizen_cannot_view_another_citizens_application(client):
    a, b = _two_citizens(client)
    _citizen_login(client, "9500000001")
    assert client.get("/application/%d" % a).status_code == 200
    r = client.get("/application/%d" % b)
    assert r.status_code in (403, 404)
    assert b"9500000002" not in r.data


def test_ack_pdf_not_public(client):
    a, b = _two_citizens(client)
    with appmod.app.test_client() as stranger:
        assert stranger.get("/ack/%d.pdf" % b).status_code in (302, 403, 404)


def test_citizen_cannot_approve_own_application(client):
    a, _ = _two_citizens(client)
    _citizen_login(client, "9500000001")
    r = client.post("/admin/approve/%d" % a)
    assert r.status_code == 403
    assert db_one("SELECT status FROM applications WHERE id=%s", (a,))[0] == "PENDING"


def test_citizen_cannot_reject_others(client):
    _, b = _two_citizens(client)
    _citizen_login(client, "9500000001")
    assert client.post("/admin/reject/%d" % b).status_code == 403
    assert db_one("SELECT status FROM applications WHERE id=%s", (b,))[0] == "PENDING"


def test_admin_can_still_approve(client):
    a, _ = _two_citizens(client)
    with appmod.app.test_client() as admin:
        admin.post("/admin", data={"username": "admin", "password": appmod.ADMIN_PASSWORD})
        admin.post("/admin/approve/%d" % a)
    assert db_one("SELECT status FROM applications WHERE id=%s", (a,))[0] == "APPROVED"
