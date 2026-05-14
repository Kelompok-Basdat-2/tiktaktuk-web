-- ============================================================
-- TK04 Trigger #2 — Venue Validation
-- ============================================================
--  1. Prevent duplicate venue name in the same city (case-insensitive)
--     on INSERT or UPDATE.
--  2. Prevent deleting a venue that still has active events
--     (event_datetime >= CURRENT_TIMESTAMP).
-- ============================================================

-- ── Trigger 2.1: Prevent duplicate venue name in the same city ─────────────

CREATE OR REPLACE FUNCTION check_venue_duplicate()
RETURNS TRIGGER AS $$
DECLARE
    existing_id VARCHAR(50);
BEGIN
    IF NEW.venue_name IS NULL OR NEW.city IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT v.venue_id
    INTO existing_id
    FROM VENUE v
    WHERE LOWER(v.venue_name) = LOWER(NEW.venue_name)
      AND LOWER(v.city) = LOWER(NEW.city)
      AND v.venue_id <> NEW.venue_id
    LIMIT 1;

    IF existing_id IS NOT NULL THEN
        RAISE EXCEPTION 'Venue "%" di kota "%" sudah terdaftar dengan ID %.',
            NEW.venue_name, NEW.city, existing_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_venue_duplicate ON VENUE;

CREATE TRIGGER trg_check_venue_duplicate
BEFORE INSERT OR UPDATE ON VENUE
FOR EACH ROW
EXECUTE FUNCTION check_venue_duplicate();


-- ── Trigger 2.2: Prevent deleting venue with active events ─────────────────

CREATE OR REPLACE FUNCTION check_venue_before_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM EVENT e
        WHERE e.venue_id = OLD.venue_id
          AND e.event_datetime >= CURRENT_TIMESTAMP
    ) THEN
        RAISE EXCEPTION 'Venue "%" masih memiliki event aktif sehingga tidak dapat dihapus.',
            OLD.venue_name;
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_venue_delete ON VENUE;

CREATE TRIGGER trg_check_venue_delete
BEFORE DELETE ON VENUE
FOR EACH ROW
EXECUTE FUNCTION check_venue_before_delete();
