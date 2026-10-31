-- Synthetic demo seed for local/dev (NOT production citizen data).
-- Copy to seed/seed.sql before `docker compose up`:
--   cp seed/seed.example.sql seed/seed.sql
-- Production deploy uses the department handout seed via deploy/deploy.sh SEED=...

-- Demo applications (two past the 15-day SLA for deemed-approval smoke tests)
INSERT INTO applications (
    application_no, applicant_name, mobile, dob, gender, marital_status,
    husband_name, husband_employer, village, block, bank_account, ifsc,
    doc_path, status, submitted_at, decided_at, decided_by
) VALUES
(
    'SSP26000101', 'रामेश्वर प्रसाद', '9000000001', '1950-08-15', 'Male', 'Married',
    '', '', 'Sonari Gaon', 'Sonari', '123456789012', 'SBIN0001234',
    NULL, 'PENDING', NOW() - INTERVAL '20 days', NULL, NULL
),
(
    'SSP26000102', 'Sunita Devi', '9000000002', '1948-03-05', 'Female', 'Widowed',
    'Late Hari Prasad', '', 'Rajapara', 'Rajapara', '234567890123', 'SBIN0002345',
    NULL, 'PENDING', NOW() - INTERVAL '5 days', NULL, NULL
),
(
    'SSP26000103', 'Abdul Rahman', '9000000003', '1955-12-01', 'Male', 'Married',
    '', '', 'Borgaon', 'Borgaon', '345678901234', 'UBIN0003456',
    NULL, 'APPROVED', NOW() - INTERVAL '30 days', NOW() - INTERVAL '10 days', 'assessor'
),
(
    'SSP26000104', 'Lakshmi Bai', '9000000004', '1945-01-20', 'Female', 'Married',
    'Ramesh Bai', '', 'Namti', 'Namti', '456789012345', 'PUNB0004567',
    NULL, 'PENDING', NOW() - INTERVAL '16 days', NULL, NULL
);

-- Status portal passwords = DOB as DDMMYYYY, hashed with SHA-256 (same as app.hash_password)
INSERT INTO portal_users (mobile, password_hash) VALUES
('9000000001', '14dbb837e16b963269d929704c565846f47e835fea443950cc11b62634ed0e4d'),
('9000000002', 'b65f66e9e12a02b1ae2134cfe08b68d9438a89294638267ba323626c0d10a5d4'),
('9000000003', '4c12ec78d8147a7317317fcceffa248befaca20bcc2a0c1076ed028760de26f0'),
('9000000004', 'e1b29fe7f0584bb9d1ee4550faf86facbd5f6f0eda5575b39d4ada87c568103f');
