-- ALTER TABLE log_records ALTER COLUMN union_id DROP NOT NULL;
ALTER TABLE log_records ALTER COLUMN union_id DROP NOT NULL;
ALTER TABLE log_records ADD COLUMN username VARCHAR(64) NULL;
ALTER TABLE log_records ADD COLUMN detection_type VARCHAR(64) NULL;
CREATE INDEX idx_log_records_username ON log_records(username);