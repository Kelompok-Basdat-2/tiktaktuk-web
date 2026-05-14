-- ============================================================
-- TK04 Trigger #5 — Seat & Ticket Validation
-- ============================================================
--  1. BEFORE DELETE on SEAT — blocks deletion if seat is occupied
--  2. BEFORE INSERT on TICKET — blocks creation if category quota is full
-- Error messages MUST come from these triggers — NOT from Python logic.
-- ============================================================

-- ── Trigger 5.1: Prevent deleting occupied seats ─────────────────────────────

CREATE OR REPLACE FUNCTION check_seat_before_delete()
RETURNS TRIGGER AS $$
DECLARE
    seat_label TEXT;
BEGIN
    IF EXISTS (SELECT 1 FROM HAS_RELATIONSHIP WHERE seat_id = OLD.seat_id) THEN
        seat_label := OLD.section || ' - Baris ' || OLD.row_number || ' No. ' || OLD.seat_number;
        RAISE EXCEPTION 'Error: Kursi % tidak dapat dihapus karena sudah terisi.', seat_label;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_seat_delete ON SEAT;

CREATE TRIGGER trg_check_seat_delete
BEFORE DELETE ON SEAT
FOR EACH ROW
EXECUTE FUNCTION check_seat_before_delete();


-- ── Trigger 5.2: Prevent ticket creation when quota is full ──────────────────

CREATE OR REPLACE FUNCTION check_ticket_quota()
RETURNS TRIGGER AS $$
DECLARE
    cat_quota  INTEGER;
    cat_used   INTEGER;
    cat_name   VARCHAR(50);
BEGIN
    -- Get quota and current usage for this category
    SELECT tc.quota, tc.category_name
    INTO cat_quota, cat_name
    FROM TICKET_CATEGORY tc
    WHERE tc.category_id = NEW.tcategory_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Error: Kategori tiket tidak ditemukan.';
    END IF;

    SELECT COUNT(*) INTO cat_used
    FROM TICKET
    WHERE tcategory_id = NEW.tcategory_id;

    IF cat_used >= cat_quota THEN
        RAISE EXCEPTION 'Error: Kuota kategori tiket "%" sudah penuh. Tidak dapat membuat tiket baru.', cat_name;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_ticket_quota ON TICKET;

CREATE TRIGGER trg_check_ticket_quota
BEFORE INSERT ON TICKET
FOR EACH ROW
EXECUTE FUNCTION check_ticket_quota();
