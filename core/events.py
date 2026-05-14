"""
Event query functions — all raw SQL, zero ORM.
"""

from django.db import connection


def _next_event_id() -> str:
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM EVENT')
        count = c.fetchone()[0] + 1
    return f'evt-{count:03d}'


def _normalize_datetime(value: str) -> str:
    return value.replace('T', ' ') if value else value


def get_all_events(search: str = '', organizer_id: str = '') -> list[dict]:
    sql = '''
        SELECT e.event_id, e.event_title, e.event_datetime,
               e.venue_id, v.venue_name, v.city,
               e.organizer_id, o.organizer_name,
               (SELECT MIN(price) FROM TICKET_CATEGORY tc WHERE tc.tevent_id = e.event_id) AS min_price
        FROM EVENT e
        JOIN VENUE v ON e.venue_id = v.venue_id
        JOIN ORGANIZER o ON e.organizer_id = o.organizer_id
    '''
    params = []
    conditions = []

    if search:
        conditions.append(
            '(LOWER(e.event_title) LIKE %s OR LOWER(v.venue_name) LIKE %s OR LOWER(o.organizer_name) LIKE %s)'
        )
        search_param = f'%{search.lower()}%'
        params += [search_param, search_param, search_param]

    if organizer_id:
        conditions.append('e.organizer_id = %s')
        params.append(organizer_id)

    if conditions:
        sql += ' WHERE ' + ' AND '.join(conditions)

    sql += ' ORDER BY e.event_datetime DESC'

    with connection.cursor() as c:
        c.execute(sql, params)
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_event_by_id(event_id: str) -> dict | None:
    with connection.cursor() as c:
        c.execute(
            '''SELECT event_id, event_title, event_datetime, venue_id, organizer_id
               FROM EVENT WHERE event_id = %s''',
            [event_id],
        )
        row = c.fetchone()
    if not row:
        return None
    columns = ['event_id', 'event_title', 'event_datetime', 'venue_id', 'organizer_id']
    return dict(zip(columns, row))


def get_organizers_for_dropdown() -> list[dict]:
    with connection.cursor() as c:
        c.execute(
            'SELECT organizer_id, organizer_name FROM ORGANIZER ORDER BY organizer_name'
        )
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def create_event(event_title: str, event_datetime: str, venue_id: str, organizer_id: str) -> str:
    event_id = _next_event_id()
    with connection.cursor() as c:
        c.execute(
            '''INSERT INTO EVENT (event_id, event_datetime, event_title, venue_id, organizer_id)
               VALUES (%s, %s, %s, %s, %s)''',
            [event_id, _normalize_datetime(event_datetime), event_title, venue_id, organizer_id],
        )
    return event_id


def update_event(event_id: str, event_title: str, event_datetime: str,
                 venue_id: str, organizer_id: str) -> None:
    with connection.cursor() as c:
        c.execute(
            '''UPDATE EVENT
               SET event_datetime = %s, event_title = %s, venue_id = %s, organizer_id = %s
               WHERE event_id = %s''',
            [_normalize_datetime(event_datetime), event_title, venue_id, organizer_id, event_id],
        )
