"""
Venue query functions — all raw SQL, zero ORM.
"""

from django.db import connection


def _next_venue_id() -> str:
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM VENUE')
        count = c.fetchone()[0] + 1
    return f'ven-{count:03d}'


def get_all_venues(search: str = '') -> list[dict]:
    sql = '''
        SELECT v.venue_id, v.venue_name, v.capacity, v.address, v.city,
               COALESCE(COUNT(e.event_id), 0) AS event_count,
               COALESCE(SUM(CASE WHEN e.event_datetime >= NOW() THEN 1 ELSE 0 END), 0) AS active_event_count
        FROM VENUE v
        LEFT JOIN EVENT e ON e.venue_id = v.venue_id
    '''
    params = []
    if search:
        sql += ' WHERE LOWER(v.venue_name) LIKE %s OR LOWER(v.city) LIKE %s OR LOWER(v.address) LIKE %s'
        search_param = f'%{search.lower()}%'
        params = [search_param, search_param, search_param]

    sql += ' GROUP BY v.venue_id, v.venue_name, v.capacity, v.address, v.city'
    sql += ' ORDER BY v.venue_name ASC'

    with connection.cursor() as c:
        c.execute(sql, params)
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_venue_by_id(venue_id: str) -> dict | None:
    with connection.cursor() as c:
        c.execute(
            'SELECT venue_id, venue_name, capacity, address, city FROM VENUE WHERE venue_id = %s',
            [venue_id],
        )
        row = c.fetchone()
    if not row:
        return None
    columns = ['venue_id', 'venue_name', 'capacity', 'address', 'city']
    return dict(zip(columns, row))


def get_venue_stats() -> dict:
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*), COUNT(DISTINCT city), COALESCE(AVG(capacity), 0) FROM VENUE')
        total, city_count, avg_capacity = c.fetchone()

        c.execute('''
            SELECT COUNT(*)
            FROM VENUE v
            LEFT JOIN EVENT e ON e.venue_id = v.venue_id
            WHERE e.event_id IS NULL
        ''')
        no_event_count = c.fetchone()[0]

    return {
        'total_venues': total,
        'city_count': city_count,
        'avg_capacity': int(avg_capacity or 0),
        'no_event_count': no_event_count,
    }


def create_venue(venue_name: str, capacity: int, address: str, city: str) -> str:
    venue_id = _next_venue_id()
    with connection.cursor() as c:
        c.execute(
            '''INSERT INTO VENUE (venue_id, venue_name, capacity, address, city)
               VALUES (%s, %s, %s, %s, %s)''',
            [venue_id, venue_name, capacity, address, city],
        )
    return venue_id


def update_venue(venue_id: str, venue_name: str, capacity: int, address: str, city: str) -> None:
    with connection.cursor() as c:
        c.execute(
            '''UPDATE VENUE
               SET venue_name = %s, capacity = %s, address = %s, city = %s
               WHERE venue_id = %s''',
            [venue_name, capacity, address, city, venue_id],
        )


def delete_venue(venue_id: str) -> None:
    with connection.cursor() as c:
        c.execute('DELETE FROM VENUE WHERE venue_id = %s', [venue_id])
