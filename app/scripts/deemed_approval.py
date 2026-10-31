# -*- coding: utf-8 -*-
"""
Nightly deemed-approval job.

Under the Purvanchal Right to Public Services Act, an application not processed
within the statutory SLA stands approved. This job marks such applications
DEEMED_APPROVED and notifies the applicant by SMS.

Scheduled via cron, 02:00 daily. See deploy/crontab.
"""

import os
import sys
import configparser
from datetime import datetime, timedelta

import psycopg2
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# F-03: config/settings.ini was consolidated into config/app.ini in March 2026
# (CR-2026-031) but this job kept opening settings.ini, so it crashed every
# night from 2026-03-15. Read the same file the web app reads (legacy file
# still honoured if present) and fail loudly if neither exists.
config = configparser.ConfigParser()
CONFIG_PATHS = [os.path.join(BASE_DIR, "config", "app.ini"),
                os.path.join(BASE_DIR, "config", "settings.ini")]
if not config.read(CONFIG_PATHS):
    raise SystemExit("deemed approval: no config found in %s" % CONFIG_PATHS)


def cfg(section, key):
    return os.environ.get("SEWASETU_%s_%s" % (section.upper(), key.upper()),
                          config.get(section, key))


SLA_DAYS = int(cfg("pension", "sla_days"))
SMS_GATEWAY_URL = cfg("app", "sms_gateway_url")


def main():
    conn = psycopg2.connect(
        host=cfg("database", "host"),
        port=cfg("database", "port"),
        dbname=cfg("database", "name"),
        user=cfg("database", "user"),
        password=cfg("database", "password"),
    )
    cur = conn.cursor()
    cutoff = datetime.now() - timedelta(days=SLA_DAYS)
    cur.execute(
        """UPDATE applications
           SET status = 'DEEMED_APPROVED', decided_at = %s, decided_by = 'RTPS-AUTO'
           WHERE status = 'PENDING' AND submitted_at < %s
           RETURNING application_no, mobile""",
        (datetime.now(), cutoff))
    rows = cur.fetchall()
    conn.commit()
    for app_no, mobile in rows:
        try:
            requests.post(SMS_GATEWAY_URL + "/api/send", json={
                "to": mobile,
                "text": "Sewa Setu: your pension application %s stands approved "
                        "under the RTPS Act." % app_no}, timeout=5)
        except Exception:
            pass
    print("%s deemed approval: %d applications approved"
          % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(rows)))
    cur.close()
    conn.close()


if __name__ == "__main__":
    sys.exit(main())
