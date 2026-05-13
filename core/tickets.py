"""
Ticket and Seat query functions — all raw SQL, zero ORM.
"""

from django.db import connection


# ═══════════════════════════════════════════════════════════════════════════════
# Ticket queries
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_tickets(search: str = '', event_id: str = '') -> list[dict]:
    """All tickets with joins. Admin view."""
    sql = '''
        SELECT t.ticket_id, t.ticket_code, t.tcategory_id, t.torder_id,
               tc.category_name, tc.price,
               o.order_date, o.payment_status,
               c.full_name AS customer_name,
               e.event_title, e.event_id,
               s.section, s.seat_number, s.row_number, s.seat_id
        FROM TICKET t
        JOIN TICKET_CATEGORY tc ON t.tcategory_id = tc.category_id
        JOIN "ORDER" o ON t.torder_id = o.order_id
        JOIN CUSTOMER c ON o.customer_id = c.customer_id
        JOIN EVENT e ON tc.tevent_id = e.event_id
        LEFT JOIN HAS_RELATIONSHIP hr ON t.ticket_id = hr.ticket_id
        LEFT JOIN SEAT s ON hr.seat_id = s.seat_id
    '''
    params = []
    conditions = []
    if search:
        conditions.append('LOWER(t.ticket_code) LIKE %s')
        params.append(f'%{search.lower()}%')
    if event_id:
        conditions.append('e.event_id = %s')
        params.append(event_id)

    if conditions:
        sql += ' WHERE ' + ' AND '.join(conditions)
    sql += ' ORDER BY t.ticket_code'

    with connection.cursor() as c:
        c.execute(sql, params)
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_tickets_by_organizer(user_id: str, search: str = '') -> list[dict]:
    """Tickets for events owned by this organizer."""
    sql = '''
        SELECT t.ticket_id, t.ticket_code, t.tcategory_id, t.torder_id,
               tc.category_name, tc.price,
               o.order_date, o.payment_status,
               c.full_name AS customer_name,
               e.event_title, e.event_id,
               s.section, s.seat_number, s.row_number, s.seat_id
        FROM TICKET t
        JOIN TICKET_CATEGORY tc ON t.tcategory_id = tc.category_id
        JOIN "ORDER" o ON t.torder_id = o.order_id
        JOIN CUSTOMER c ON o.customer_id = c.customer_id
        JOIN EVENT e ON tc.tevent_id = e.event_id
        JOIN ORGANIZER org ON e.organizer_id = org.organizer_id
        LEFT JOIN HAS_RELATIONSHIP hr ON t.ticket_id = hr.ticket_id
        LEFT JOIN SEAT s ON hr.seat_id = s.seat_id
        WHERE org.user_id = %s
    '''
    params = [user_id]
    if search:
        sql += ' AND LOWER(t.ticket_code) LIKE %s'
        params.append(f'%{search.lower()}%')
    sql += ' ORDER BY t.ticket_code'

    with connection.cursor() as c:
        c.execute(sql, params)
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_tickets_by_customer(user_id: str, search: str = '') -> list[dict]:
    """Tickets belonging to this customer."""
    sql = '''
        SELECT t.ticket_id, t.ticket_code, t.tcategory_id, t.torder_id,
               tc.category_name, tc.price,
               o.order_date, o.payment_status,
               e.event_title, e.event_id,
               s.section, s.seat_number, s.row_number, s.seat_id
        FROM TICKET t
        JOIN TICKET_CATEGORY tc ON t.tcategory_id = tc.category_id
        JOIN "ORDER" o ON t.torder_id = o.order_id
        JOIN CUSTOMER c ON o.customer_id = c.customer_id
        JOIN EVENT e ON tc.tevent_id = e.event_id
        LEFT JOIN HAS_RELATIONSHIP hr ON t.ticket_id = hr.ticket_id
        LEFT JOIN SEAT s ON hr.seat_id = s.seat_id
        WHERE c.user_id = %s
    '''
    params = [user_id]
    if search:
        sql += ' AND LOWER(t.ticket_code) LIKE %s'
        params.append(f'%{search.lower()}%')
    sql += ' ORDER BY t.ticket_code'

    with connection.cursor() as c:
        c.execute(sql, params)
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_ticket_by_id(ticket_id: str) -> dict | None:
    sql = '''
        SELECT t.ticket_id, t.ticket_code, t.tcategory_id, t.torder_id,
               tc.category_name, tc.price, tc.tevent_id,
               o.order_date, o.payment_status, o.customer_id,
               c.full_name AS customer_name,
               e.event_title, e.event_id,
               s.section, s.seat_number, s.row_number, s.seat_id
        FROM TICKET t
        JOIN TICKET_CATEGORY tc ON t.tcategory_id = tc.category_id
        JOIN "ORDER" o ON t.torder_id = o.order_id
        JOIN CUSTOMER c ON o.customer_id = c.customer_id
        JOIN EVENT e ON tc.tevent_id = e.event_id
        LEFT JOIN HAS_RELATIONSHIP hr ON t.ticket_id = hr.ticket_id
        LEFT JOIN SEAT s ON hr.seat_id = s.seat_id
        WHERE t.ticket_id = %s
    '''
    with connection.cursor() as c:
        c.execute(sql, [ticket_id])
        row = c.fetchone()
    if not row:
        return None
    columns = [col[0] for col in c.description]
    return dict(zip(columns, row))


def _next_ticket_code() -> str:
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM TICKET')
        count = c.fetchone()[0]
    return f'TKT-{count + 1:04d}'


def create_ticket(torder_id: str, tcategory_id: str) -> str:
    """Insert ticket. Returns ticket_id. Seat assigned separately."""
    ticket_id = f'tkt-{_next_ticket_suffix()}'
    code = _next_ticket_code()

    with connection.cursor() as c:
        c.execute(
            '''INSERT INTO TICKET (ticket_id, ticket_code, tcategory_id, torder_id)
               VALUES (%s, %s, %s, %s)''',
            [ticket_id, code, tcategory_id, torder_id],
        )
    return ticket_id


def _next_ticket_suffix() -> str:
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM TICKET')
        count = c.fetchone()[0] + 1
    return f'{count:03d}'


def assign_seat_to_ticket(ticket_id: str, seat_id: str) -> None:
    with connection.cursor() as c:
        c.execute(
            'INSERT INTO HAS_RELATIONSHIP (seat_id, ticket_id) VALUES (%s, %s)',
            [seat_id, ticket_id],
        )


def update_ticket_seat(ticket_id: str, seat_id: str | None) -> None:
    """Update or remove seat assignment for a ticket."""
    with connection.cursor() as c:
        c.execute('DELETE FROM HAS_RELATIONSHIP WHERE ticket_id = %s', [ticket_id])
        if seat_id:
            c.execute(
                'INSERT INTO HAS_RELATIONSHIP (seat_id, ticket_id) VALUES (%s, %s)',
                [seat_id, ticket_id],
            )


def delete_ticket(ticket_id: str) -> None:
    with connection.cursor() as c:
        c.execute('DELETE FROM HAS_RELATIONSHIP WHERE ticket_id = %s', [ticket_id])
        c.execute('DELETE FROM TICKET WHERE ticket_id = %s', [ticket_id])


def get_orders_for_dropdown() -> list[dict]:
    """Orders with customer name and event title for create-ticket dropdown."""
    with connection.cursor() as c:
        c.execute('''
            SELECT o.order_id,
                   c.full_name AS customer_name,
                   o.payment_status
            FROM "ORDER" o
            JOIN CUSTOMER c ON o.customer_id = c.customer_id
            ORDER BY o.order_date DESC
        ''')
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_categories_for_event(event_id: str) -> list[dict]:
    """Ticket categories for an event with used count."""
    with connection.cursor() as c:
        c.execute('''
            SELECT tc.category_id, tc.category_name, tc.price, tc.quota,
                   (SELECT COUNT(*) FROM TICKET t WHERE t.tcategory_id = tc.category_id) AS used
            FROM TICKET_CATEGORY tc
            WHERE tc.tevent_id = %s
            ORDER BY tc.price DESC
        ''', [event_id])
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_seats_for_venue(venue_id: str) -> list[dict]:
    """Available seats for a venue (not yet assigned to any ticket)."""
    with connection.cursor() as c:
        c.execute('''
            SELECT s.seat_id, s.section, s.seat_number, s.row_number
            FROM SEAT s
            WHERE s.venue_id = %s
              AND s.seat_id NOT IN (
                  SELECT seat_id FROM HAS_RELATIONSHIP
              )
            ORDER BY s.section, s.row_number, s.seat_number
        ''', [venue_id])
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_event_for_ticket_category(category_id: str) -> dict | None:
    with connection.cursor() as c:
        c.execute('''
            SELECT e.event_id, e.event_title, e.venue_id
            FROM EVENT e
            JOIN TICKET_CATEGORY tc ON tc.tevent_id = e.event_id
            WHERE tc.category_id = %s
        ''', [category_id])
        row = c.fetchone()
    if row:
        return {'event_id': row[0], 'event_title': row[1], 'venue_id': row[2]}
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Seat queries
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_seats() -> list[dict]:
    """All seats with venue name and occupancy status."""
    with connection.cursor() as c:
        c.execute('''
            SELECT s.seat_id, s.section, s.seat_number, s.row_number,
                   s.venue_id, v.venue_name, v.city,
                   CASE WHEN hr.seat_id IS NOT NULL THEN true ELSE false END AS occupied
            FROM SEAT s
            JOIN VENUE v ON s.venue_id = v.venue_id
            LEFT JOIN HAS_RELATIONSHIP hr ON s.seat_id = hr.seat_id
            ORDER BY v.venue_name, s.section, s.row_number, s.seat_number
        ''')
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_seats_by_organizer(user_id: str) -> list[dict]:
    """Seats for venues owned by this organizer."""
    with connection.cursor() as c:
        c.execute('''
            SELECT s.seat_id, s.section, s.seat_number, s.row_number,
                   s.venue_id, v.venue_name, v.city,
                   CASE WHEN hr.seat_id IS NOT NULL THEN true ELSE false END AS occupied
            FROM SEAT s
            JOIN VENUE v ON s.venue_id = v.venue_id
            JOIN ORGANIZER org ON org.organizer_id IN (
                SELECT organizer_id FROM EVENT WHERE venue_id = s.venue_id
            )
            LEFT JOIN HAS_RELATIONSHIP hr ON s.seat_id = hr.seat_id
            WHERE org.user_id = %s
            ORDER BY v.venue_name, s.section, s.row_number, s.seat_number
        ''', [user_id])
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_seat_by_id(seat_id: str) -> dict | None:
    with connection.cursor() as c:
        c.execute('''
            SELECT s.seat_id, s.section, s.seat_number, s.row_number,
                   s.venue_id, v.venue_name,
                   CASE WHEN hr.seat_id IS NOT NULL THEN true ELSE false END AS occupied
            FROM SEAT s
            JOIN VENUE v ON s.venue_id = v.venue_id
            LEFT JOIN HAS_RELATIONSHIP hr ON s.seat_id = hr.seat_id
            WHERE s.seat_id = %s
        ''', [seat_id])
        row = c.fetchone()
    if not row:
        return None
    columns = [col[0] for col in c.description]
    return dict(zip(columns, row))


def is_seat_occupied(seat_id: str) -> bool:
    with connection.cursor() as c:
        c.execute(
            'SELECT 1 FROM HAS_RELATIONSHIP WHERE seat_id = %s LIMIT 1',
            [seat_id],
        )
        return c.fetchone() is not None


def create_seat(section: str, seat_number: str, row_number: str, venue_id: str) -> str:
    seat_id = _next_seat_id()
    with connection.cursor() as c:
        c.execute(
            '''INSERT INTO SEAT (seat_id, section, seat_number, row_number, venue_id)
               VALUES (%s, %s, %s, %s, %s)''',
            [seat_id, section, seat_number, row_number, venue_id],
        )
    return seat_id


def _next_seat_id() -> str:
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM SEAT')
        count = c.fetchone()[0] + 1
    return f'seat-{count:03d}'


def update_seat(seat_id: str, section: str, seat_number: str,
                row_number: str, venue_id: str) -> None:
    with connection.cursor() as c:
        c.execute(
            '''UPDATE SEAT SET section=%s, seat_number=%s, row_number=%s, venue_id=%s
               WHERE seat_id=%s''',
            [section, seat_number, row_number, venue_id, seat_id],
        )


def delete_seat(seat_id: str) -> None:
    with connection.cursor() as c:
        c.execute('DELETE FROM SEAT WHERE seat_id = %s', [seat_id])


def get_venues_for_dropdown() -> list[dict]:
    with connection.cursor() as c:
        c.execute(
            'SELECT venue_id, venue_name, city FROM VENUE ORDER BY venue_name'
        )
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_events_for_dropdown() -> list[dict]:
    with connection.cursor() as c:
        c.execute(
            'SELECT event_id, event_title, event_datetime FROM EVENT ORDER BY event_datetime DESC'
        )
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]
