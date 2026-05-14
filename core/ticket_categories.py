"""
Ticket Category query functions — all raw SQL, zero ORM.
Fitur 11 (CUD Ticket Category - Admin/Organizer) & Fitur 12 (R - semua user).
"""

import uuid
from django.db import connection


# ═══════════════════════════════════════════════════════════════════════════════
# Read
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_ticket_categories(search: str = '', event_id: str = '') -> list[dict]:
    """
    Return all ticket categories joined with event name.
    Ordered by event_title ASC, then category_name ASC.
    """
    sql = '''
        SELECT tc.category_id, tc.category_name, tc.quota, tc.price,
               tc.tevent_id, e.event_title
        FROM TICKET_CATEGORY tc
        JOIN EVENT e ON tc.tevent_id = e.event_id
    '''
    params = []
    conditions = []
    if search:
        conditions.append(
            '(LOWER(tc.category_name) LIKE %s OR LOWER(e.event_title) LIKE %s)'
        )
        params += [f'%{search.lower()}%', f'%{search.lower()}%']
    if event_id:
        conditions.append('tc.tevent_id = %s')
        params.append(event_id)

    if conditions:
        sql += ' WHERE ' + ' AND '.join(conditions)
    sql += ' ORDER BY e.event_title ASC, tc.category_name ASC'

    with connection.cursor() as c:
        c.execute(sql, params)
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_ticket_category_by_id(category_id: str) -> dict | None:
    sql = '''
        SELECT tc.category_id, tc.category_name, tc.quota, tc.price,
               tc.tevent_id, e.event_title
        FROM TICKET_CATEGORY tc
        JOIN EVENT e ON tc.tevent_id = e.event_id
        WHERE tc.category_id = %s
    '''
    with connection.cursor() as c:
        c.execute(sql, [category_id])
        row = c.fetchone()
    if not row:
        return None
    columns = ['category_id', 'category_name', 'quota', 'price', 'tevent_id', 'event_title']
    return dict(zip(columns, row))


def get_ticket_category_stats() -> dict:
    """Stats for the header cards."""
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM TICKET_CATEGORY')
        total = c.fetchone()[0]

        c.execute('SELECT COALESCE(SUM(quota), 0) FROM TICKET_CATEGORY')
        total_quota = c.fetchone()[0]

        c.execute('SELECT COALESCE(MAX(price), 0) FROM TICKET_CATEGORY')
        max_price = c.fetchone()[0]

    return {
        'total_categories': total,
        'total_quota': int(total_quota),
        'max_price': int(max_price),
    }


def get_remaining_quota(event_id: str) -> list[dict]:
    """
    Sisa kuota per ticket category untuk suatu event.
    Trigger 2: Menampilkan Sisa Kuota Ticket Category berdasarkan tevent_id.
    """
    sql = '''
        SELECT tc.category_id, tc.category_name, tc.quota,
               tc.quota - COALESCE(
                   (SELECT COUNT(*) FROM TICKET t WHERE t.tcategory_id = tc.category_id),
                   0
               ) AS remaining_quota,
               tc.price
        FROM TICKET_CATEGORY tc
        WHERE tc.tevent_id = %s
        ORDER BY tc.category_name ASC
    '''
    with connection.cursor() as c:
        c.execute(sql, [event_id])
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


# ═══════════════════════════════════════════════════════════════════════════════
# Venue capacity validation helper
# ═══════════════════════════════════════════════════════════════════════════════

def get_venue_capacity_for_event(event_id: str) -> int | None:
    """Return venue capacity for the given event."""
    with connection.cursor() as c:
        c.execute('''
            SELECT v.capacity
            FROM VENUE v
            JOIN EVENT e ON e.venue_id = v.venue_id
            WHERE e.event_id = %s
        ''', [event_id])
        row = c.fetchone()
    return row[0] if row else None


def get_total_quota_for_event(event_id: str, exclude_category_id: str = '') -> int:
    """Sum of quota for all ticket categories of an event (excluding one for update)."""
    sql = 'SELECT COALESCE(SUM(quota), 0) FROM TICKET_CATEGORY WHERE tevent_id = %s'
    params = [event_id]
    if exclude_category_id:
        sql += ' AND category_id != %s'
        params.append(exclude_category_id)
    with connection.cursor() as c:
        c.execute(sql, params)
        return int(c.fetchone()[0])


def category_name_exists_in_event(
    category_name: str, event_id: str, exclude_category_id: str = ''
) -> bool:
    """
    Returns True if a category with the same name (case-insensitive)
    already exists for the given event.
    Pass exclude_category_id when updating so we don't flag the row itself.
    """
    sql = '''
        SELECT 1 FROM TICKET_CATEGORY
        WHERE LOWER(category_name) = LOWER(%s)
          AND tevent_id = %s
    '''
    params = [category_name, event_id]
    if exclude_category_id:
        sql += ' AND category_id != %s'
        params.append(exclude_category_id)
    with connection.cursor() as c:
        c.execute(sql, params)
        return c.fetchone() is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Create
# ═══════════════════════════════════════════════════════════════════════════════

def create_ticket_category(
    category_name: str, quota: int, price: float, tevent_id: str
) -> str:
    """Insert a new ticket category. Returns category_id."""
    category_id = str(uuid.uuid4())
    with connection.cursor() as c:
        c.execute(
            '''INSERT INTO TICKET_CATEGORY (category_id, category_name, quota, price, tevent_id)
               VALUES (%s, %s, %s, %s, %s)''',
            [category_id, category_name, quota, price, tevent_id],
        )
    return category_id


# ═══════════════════════════════════════════════════════════════════════════════
# Update
# ═══════════════════════════════════════════════════════════════════════════════

def update_ticket_category(
    category_id: str, category_name: str, quota: int, price: float
) -> None:
    with connection.cursor() as c:
        c.execute(
            '''UPDATE TICKET_CATEGORY
               SET category_name = %s, quota = %s, price = %s
               WHERE category_id = %s''',
            [category_name, quota, price, category_id],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Delete
# ═══════════════════════════════════════════════════════════════════════════════

def delete_ticket_category(category_id: str) -> None:
    """
    Delete a ticket category.
    NOTE: tickets linked to this category must be handled (FK constraint).
    If tickets exist, this will raise a DB exception — let the view handle it.
    """
    with connection.cursor() as c:
        c.execute(
            'DELETE FROM TICKET_CATEGORY WHERE category_id = %s',
            [category_id],
        )
