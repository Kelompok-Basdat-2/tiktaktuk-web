-- ============================================================
-- TK04 Trigger #1 — Username Validation (Wajib)
-- ============================================================
-- Fires BEFORE INSERT on USER_ACCOUNT.
--  1. Rejects usernames with non-alphanumeric characters (a-z, A-Z, 0-9 only)
--  2. Rejects case-insensitive duplicate usernames
-- Error messages MUST come from this trigger — NOT from Python logic.
-- ============================================================

CREATE OR REPLACE FUNCTION validate_username()
RETURNS TRIGGER AS $$
BEGIN
    -- Check 1: only alphanumeric characters allowed (a-z, A-Z, 0-9)
    IF NEW.username !~ '^[a-zA-Z0-9]+$' THEN
        RAISE EXCEPTION 'Error: Username "%" hanya boleh mengandung huruf dan angka tanpa simbol atau spasi.', NEW.username;
    END IF;

    -- Check 2: case-insensitive duplicate
    IF EXISTS (
        SELECT 1 FROM USER_ACCOUNT
        WHERE LOWER(username) = LOWER(NEW.username)
    ) THEN
        RAISE EXCEPTION 'Error: Username "%" sudah terdaftar, gunakan username lain.', NEW.username;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop old trigger if exists, then create
DROP TRIGGER IF EXISTS trg_validate_username ON USER_ACCOUNT;

CREATE TRIGGER trg_validate_username
BEFORE INSERT ON USER_ACCOUNT
FOR EACH ROW
EXECUTE FUNCTION validate_username();
