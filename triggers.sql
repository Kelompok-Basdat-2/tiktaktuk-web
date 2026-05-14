-- ============================================================
-- TikTakTuk TK04 — SQL Triggers
-- ============================================================


-- ============================================================
-- TRIGGER 1: Validasi Duplikasi artist_id + event_id pada EVENT_ARTIST
--
-- Kondisi yang dicek saat INSERT ke EVENT_ARTIST:
--   1. artist_id harus ada di tabel ARTIST
--   2. event_id harus ada di tabel EVENT
--   3. Pasangan (event_id, artist_id) belum boleh ada di EVENT_ARTIST
--
-- Pesan error:
--   "ERROR: Artist dengan ID <artist_id> tidak ditemukan."
--   "ERROR: Event dengan ID <event_id> tidak ditemukan."
--   "ERROR: Artist "<name>" sudah terdaftar pada event "<event_title>"."
-- ============================================================

CREATE OR REPLACE FUNCTION validate_event_artist_insert()
RETURNS TRIGGER AS $$
DECLARE
    v_artist_name  VARCHAR(200);
    v_event_title  VARCHAR(200);
BEGIN
    -- 1. Cek artist_id ada di tabel ARTIST
    SELECT name INTO v_artist_name
    FROM ARTIST
    WHERE artist_id = NEW.artist_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERROR: Artist dengan ID % tidak ditemukan.', NEW.artist_id;
    END IF;

    -- 2. Cek event_id ada di tabel EVENT
    SELECT event_title INTO v_event_title
    FROM EVENT
    WHERE event_id = NEW.event_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERROR: Event dengan ID % tidak ditemukan.', NEW.event_id;
    END IF;

    -- 3. Cek duplikasi (artist yang sama di event yang sama)
    IF EXISTS (
        SELECT 1 FROM EVENT_ARTIST
        WHERE event_id  = NEW.event_id
          AND artist_id = NEW.artist_id
    ) THEN
        RAISE EXCEPTION 'ERROR: Artist "%" sudah terdaftar pada event "%".', v_artist_name, v_event_title;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_event_artist ON EVENT_ARTIST;

CREATE TRIGGER trg_validate_event_artist
    BEFORE INSERT ON EVENT_ARTIST
    FOR EACH ROW
    EXECUTE FUNCTION validate_event_artist_insert();


-- ============================================================
-- TRIGGER 2 (Stored Function): Menampilkan Sisa Kuota Ticket Category
--             berdasarkan tevent_id
--
-- Mengembalikan tabel berisi semua kategori tiket suatu event
-- beserta sisa kuota (quota - jumlah tiket terjual).
--
-- Jika event_id tidak ditemukan:
--   "ERROR: Event dengan ID <event_id> tidak ditemukan."
-- ============================================================

CREATE OR REPLACE FUNCTION get_remaining_quota_by_event(p_event_id VARCHAR)
RETURNS TABLE (
    category_id    VARCHAR,
    category_name  VARCHAR,
    quota          INTEGER,
    remaining      BIGINT,
    price          NUMERIC
) AS $$
BEGIN
    -- Validasi: event harus ada
    IF NOT EXISTS (SELECT 1 FROM EVENT WHERE event_id = p_event_id) THEN
        RAISE EXCEPTION 'ERROR: Event dengan ID % tidak ditemukan.', p_event_id;
    END IF;

    RETURN QUERY
        SELECT
            tc.category_id,
            tc.category_name,
            tc.quota,
            (tc.quota - COALESCE(
                (SELECT COUNT(*) FROM TICKET t WHERE t.tcategory_id = tc.category_id),
                0
            ))::BIGINT AS remaining,
            tc.price
        FROM TICKET_CATEGORY tc
        WHERE tc.tevent_id = p_event_id
        ORDER BY tc.category_name ASC;
END;
$$ LANGUAGE plpgsql;
