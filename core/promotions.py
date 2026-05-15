"""
Promotion query helpers — raw SQL backend for promotion listing and usage tracking.
"""

from django.db import connection
from django.utils import timezone


def _rows_to_dicts(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _next_promotion_id() -> str:
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM PROMOTION')
        count = c.fetchone()[0] or 0
    return f'promo-{count + 1:03d}'


def get_promotions() -> list[dict]:
    with connection.cursor() as c:
        c.execute('''
            SELECT p.promotion_id, p.promo_code, p.discount_type, p.discount_value,
                   p.start_date, p.end_date, p.usage_limit,
                   COALESCE(COUNT(op.order_promotion_id), 0) AS usage_count
            FROM PROMOTION p
            LEFT JOIN ORDER_PROMOTION op ON op.promotion_id = p.promotion_id
            GROUP BY p.promotion_id
            ORDER BY p.start_date DESC, p.promo_code
        ''')
        return _rows_to_dicts(c)


def get_promotion_by_code(promo_code: str) -> dict | None:
    with connection.cursor() as c:
        c.execute(
            '''SELECT promotion_id, promo_code, discount_type, discount_value,
                      start_date, end_date, usage_limit
               FROM PROMOTION
               WHERE LOWER(promo_code) = LOWER(%s)''',
            [promo_code],
        )
        row = c.fetchone()
    if not row:
        return None
    columns = ['promotion_id', 'promo_code', 'discount_type', 'discount_value', 'start_date', 'end_date', 'usage_limit']
    return dict(zip(columns, row))


def get_promotion_by_id(promotion_id: str) -> dict | None:
    with connection.cursor() as c:
        c.execute(
            '''SELECT promotion_id, promo_code, discount_type, discount_value,
                      start_date, end_date, usage_limit
               FROM PROMOTION
               WHERE promotion_id = %s''',
            [promotion_id],
        )
        row = c.fetchone()
    if not row:
        return None
    columns = ['promotion_id', 'promo_code', 'discount_type', 'discount_value', 'start_date', 'end_date', 'usage_limit']
    return dict(zip(columns, row))


def create_promotion(
    promo_code: str,
    discount_type: str,
    discount_value: float,
    start_date,
    end_date,
    usage_limit: int,
) -> str:
    promotion_id = _next_promotion_id()
    normalized_type = (discount_type or '').strip().lower()
    with connection.cursor() as c:
        c.execute(
            '''INSERT INTO PROMOTION (
                   promotion_id, promo_code, discount_type, discount_value,
                   start_date, end_date, usage_limit
               ) VALUES (%s, %s, %s, %s, %s, %s, %s)''',
            [promotion_id, promo_code, normalized_type, discount_value, start_date, end_date, usage_limit],
        )
    return promotion_id


def update_promotion(
    promotion_id: str,
    promo_code: str,
    discount_type: str,
    discount_value: float,
    start_date,
    end_date,
    usage_limit: int,
) -> None:
    normalized_type = (discount_type or '').strip().lower()
    with connection.cursor() as c:
        c.execute(
            '''UPDATE PROMOTION
               SET promo_code = %s,
                   discount_type = %s,
                   discount_value = %s,
                   start_date = %s,
                   end_date = %s,
                   usage_limit = %s
               WHERE promotion_id = %s''',
            [promo_code, normalized_type, discount_value, start_date, end_date, usage_limit, promotion_id],
        )


def delete_promotion(promotion_id: str) -> None:
    with connection.cursor() as c:
        c.execute('DELETE FROM PROMOTION WHERE promotion_id = %s', [promotion_id])
