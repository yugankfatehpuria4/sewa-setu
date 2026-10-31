"""F-02: upload rejects JPG and files >100 KB although the page promises
'JPG or PDF, maximum 5 MB', and shows the opaque error 'ERR_VAL_47'.
Logs: 75,815 POST /upload vs 34,332 reaching /declaration."""
import pytest

from conftest import TINY_JPG, TINY_PDF, fill_form, upload, verify_mobile


def _ready(client, mobile):
    verify_mobile(client, mobile)
    fill_form(client)


def test_jpg_photo_of_document_accepted(client):
    _ready(client, "9700000001")
    r = upload(client, TINY_JPG + b"\x00" * 300_000, "voter_id.JPG")
    assert r.status_code == 302 and "/declaration" in r.headers["Location"]


def test_pdf_up_to_5mb_accepted(client):
    _ready(client, "9700000002")
    r = upload(client, TINY_PDF + b"0" * (4 * 1024 * 1024), "birth_certificate.pdf")
    assert r.status_code == 302


def test_rejection_message_is_plain_language(client):
    _ready(client, "9700000003")
    r = upload(client, b"MZ\x90\x00not a document", "proof.exe")
    assert r.status_code in (200, 400)
    assert b"ERR_VAL_47" not in r.data
    assert b"JPG or PDF" in r.data


def test_file_over_5mb_rejected(client):
    _ready(client, "9700000004")
    r = upload(client, TINY_PDF + b"0" * (5 * 1024 * 1024 + 10), "big.pdf")
    assert r.status_code != 302


def test_disguised_file_rejected(client):
    _ready(client, "9700000005")
    r = upload(client, b"<html>not a pdf</html>", "fake.pdf")
    assert r.status_code != 302


def test_path_traversal_filename_neutralised(client):
    _ready(client, "9700000006")
    upload(client, TINY_PDF, "../../etc/passwd.pdf")
    with client.session_transaction() as s:
        p = s.get("doc_path", "")
    assert ".." not in p
