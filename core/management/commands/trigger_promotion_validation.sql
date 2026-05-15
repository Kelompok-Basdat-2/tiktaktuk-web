-- ============================================================
-- TK04 Trigger #3 — Promotion Validation + Delete Protection
-- ============================================================
-- Fires BEFORE INSERT on ORDER_PROMOTION.
--  1. Rejects missing promotion IDs with a clear error message.
--  2. Rejects promotions whose usage has reached usage_limit.
--  3. Rejects promotions that are not valid for the event date(s) linked to the target order.
-- Fires BEFORE DELETE on PROMOTION.
--  4. Rejects deleting promotions that are still referenced by ORDER_PROMOTION.
-- ============================================================

CREATE OR REPLACE FUNCTION validate_order_promotion()
RETURNS TRIGGER AS $$
DECLARE
    promo_code TEXT;
    promo_start DATE;
    promo_end DATE;
    promo_limit INTEGER;
    promo_usage INTEGER;
    event_earliest DATE;
    event_latest DATE;
BEGIN
    SELECT p.promo_code, p.start_date, p.end_date, p.usage_limit
    INTO promo_code, promo_start, promo_end, promo_limit
    FROM PROMOTION p
    WHERE p.promotion_id = NEW.promotion_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Error: Promotion dengan ID % tidak ditemukan.', NEW.promotion_id;
    END IF;

    SELECT COUNT(*)
    INTO promo_usage
    FROM ORDER_PROMOTION
    WHERE promotion_id = NEW.promotion_id;

    IF promo_usage >= promo_limit THEN
        RAISE EXCEPTION 'Error: Promotion "%" telah mencapai batas maksimum penggunaan.', promo_code;
    END IF;

    SELECT MIN(e.event_datetime::date), MAX(e.event_datetime::date)
    INTO event_earliest, event_latest
    FROM TICKET t
    JOIN TICKET_CATEGORY tc ON t.tcategory_id = tc.category_id
    JOIN EVENT e ON tc.tevent_id = e.event_id
    WHERE t.torder_id = NEW.order_id;

    IF event_earliest IS NULL THEN
        RAISE EXCEPTION 'Error: Order % tidak memiliki tiket terkait untuk validasi promosi.', NEW.order_id;
    END IF;

    IF event_earliest < promo_start OR event_latest > promo_end THEN
        RAISE EXCEPTION 'Error: Promotion "%" tidak berlaku untuk tanggal event ini.', promo_code;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_order_promotion ON ORDER_PROMOTION;

CREATE TRIGGER trg_validate_order_promotion
BEFORE INSERT ON ORDER_PROMOTION
FOR EACH ROW
EXECUTE FUNCTION validate_order_promotion();


CREATE OR REPLACE FUNCTION prevent_used_promotion_delete()
RETURNS TRIGGER AS $$
DECLARE
    ref_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO ref_count
    FROM ORDER_PROMOTION
    WHERE promotion_id = OLD.promotion_id;

    IF ref_count > 0 THEN
        RAISE EXCEPTION 'Error: Promotion "%" telah digunakan oleh % order dan tidak dapat dihapus.',
            OLD.promo_code, ref_count;
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_used_promotion_delete ON PROMOTION;

CREATE TRIGGER trg_prevent_used_promotion_delete
BEFORE DELETE ON PROMOTION
FOR EACH ROW
EXECUTE FUNCTION prevent_used_promotion_delete();
