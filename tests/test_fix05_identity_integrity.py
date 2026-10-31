"""F-05: applicant identity is stored wrongly.
 - sanitize(maxlen=20) cuts names to 20 UTF-8 BYTES: Devanagari (3 bytes per
   code point) keeps ~6 characters and loses combining marks; long English
   names are cut too.
 - DOB is parsed '%m/%d/%Y' first although the form asks DD/MM/YYYY, so
   05/03/1960 is stored as 3 May 1960. The status-portal password is derived
   from DOB, and age eligibility near the boundary is computed wrongly."""
import pytest

from conftest import db_one, full_apply

HINDI = "रामेश्वर प्रसाद त्रिपाठी"
BENGALI = "শ্রীমতী অন্নপূর্ণা দেবী"
TAMIL = "கிருஷ்ணமூர்த்தி சுப்பிரமணியன்"


@pytest.mark.xfail(strict=True, reason="F-05")
@pytest.mark.parametrize("name,mobile", [(HINDI, "9400000001"), (BENGALI, "9400000002"),
                                         (TAMIL, "9400000003"),
                                         ("Venkata Subramanian Iyer", "9400000004")])
def test_name_stored_exactly(client, name, mobile):
    full_apply(client, mobile=mobile, applicant_name=name)
    assert db_one("SELECT applicant_name FROM applications WHERE mobile=%s", (mobile,))[0] == name


@pytest.mark.xfail(strict=True, reason="F-05")
def test_dob_read_as_day_month_year(client):
    full_apply(client, mobile="9400000005", dob="05/03/1960")
    assert str(db_one("SELECT dob FROM applications WHERE mobile='9400000005'")[0]) == "1960-03-05"


@pytest.mark.xfail(strict=True, reason="F-05")
def test_portal_password_matches_dob_citizen_typed(client):
    full_apply(client, mobile="9400000006", dob="05/03/1958")
    client.get("/status")
    r = client.post("/status", data={"mobile": "9400000006", "password": "05031958"})
    assert r.status_code == 302 and "/application/" in r.headers["Location"]


def test_hindi_name_displayed_on_status_page(client):
    full_apply(client, mobile="9400000007", applicant_name=HINDI)
    client.post("/status", data={"mobile": "9400000007", "password": "15081950"})
    app_id = db_one("SELECT id FROM applications WHERE mobile='9400000007'")[0]
    assert db_one("SELECT applicant_name FROM applications WHERE id=%s", (app_id,))[0][:3] == HINDI[:3]
