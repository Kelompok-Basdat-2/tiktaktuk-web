"""
Order query helpers — raw SQL backend for order listings and filtering.
"""

from django.db import connection
from django.utils import timezone


def _rows_to_dicts(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _next_order_id() -> str:
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM "ORDER"')
        count = c.fetchone()[0] or 0
    return f'ord-{count + 1:03d}'


def _next_order_promotion_id() -> str:
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM ORDER_PROMOTION')
        count = c.fetchone()[0] or 0
    return f'op-{count + 1:03d}'


def get_all_orders() -> list[dict]:
    with connection.cursor() as c:
        c.execute('''
            SELECT o.order_id, o.order_date, o.payment_status, o.total_amount,
                   c.full_name AS customer_name
            FROM "ORDER" o
            JOIN CUSTOMER c ON o.customer_id = c.customer_id
            ORDER BY o.order_date DESC
        ''')
        return _rows_to_dicts(c)


def get_orders_by_customer(user_id: str) -> list[dict]:
    with connection.cursor() as c:
        c.execute('''
            SELECT o.order_id, o.order_date, o.payment_status, o.total_amount,
                   c.full_name AS customer_name
            FROM "ORDER" o
            JOIN CUSTOMER c ON o.customer_id = c.customer_id
            WHERE c.user_id = %s
            ORDER BY o.order_date DESC
        ''', [user_id])
        return _rows_to_dicts(c)


def get_orders_by_organizer(user_id: str) -> list[dict]:
    with connection.cursor() as c:
        c.execute('''
            SELECT DISTINCT o.order_id, o.order_date, o.payment_status, o.total_amount,
                   c.full_name AS customer_name
            FROM "ORDER" o
            JOIN CUSTOMER c ON o.customer_id = c.customer_id
            JOIN TICKET t ON t.torder_id = o.order_id
            JOIN TICKET_CATEGORY tc ON t.tcategory_id = tc.category_id
            JOIN EVENT e ON tc.tevent_id = e.event_id
            JOIN ORGANIZER org ON e.organizer_id = org.organizer_id
            WHERE org.user_id = %s
            ORDER BY o.order_date DESC
        ''', [user_id])
        return _rows_to_dicts(c)


def create_order(customer_id: str, total_amount: float, payment_status: str = 'Lunas') -> str:
    order_id = _next_order_id()
    with connection.cursor() as c:
        c.execute(
            '''INSERT INTO "ORDER" (order_id, order_date, payment_status, total_amount, customer_id)
               VALUES (%s, %s, %s, %s, %s)''',
            [order_id, timezone.now(), payment_status, total_amount, customer_id],
        )
    return order_id


def apply_promotion(order_id: str, promotion_id: str) -> str:
    order_promotion_id = _next_order_promotion_id()
    with connection.cursor() as c:
        c.execute(
            '''INSERT INTO ORDER_PROMOTION (order_promotion_id, promotion_id, order_id)
               VALUES (%s, %s, %s)''',
            [order_promotion_id, promotion_id, order_id],
        )
    return order_promotion_id
