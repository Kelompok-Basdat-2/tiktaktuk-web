"""
Promotion query helpers — raw SQL backend for promotion listing and usage tracking.
"""

from django.db import connection


def _rows_to_dicts(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


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
