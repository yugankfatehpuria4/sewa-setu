-- Additive only. Speeds up status login and duplicate checks (lookup by mobile)
-- and the admin queue (status + submitted_at). Safe to run on live data.
CREATE INDEX IF NOT EXISTS idx_applications_mobile ON applications (mobile);
CREATE INDEX IF NOT EXISTS idx_applications_status_submitted ON applications (status, submitted_at);
CREATE INDEX IF NOT EXISTS idx_otps_mobile_id ON otps (mobile, id DESC);
