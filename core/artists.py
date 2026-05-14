"""
Artist query functions — all raw SQL, zero ORM.
Fitur 9 (CUD Artist - Admin) & Fitur 10 (R Artist - semua user login).
"""

import uuid
from django.db import connection


# ═══════════════════════════════════════════════════════════════════════════════
# Read
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_artists(search: str = '') -> list[dict]:
    """Return all artists ordered by name ASC."""
    sql = '''
        SELECT artist_id, name, genre
        FROM ARTIST
    '''
    params = []
    if search:
        sql += ' WHERE LOWER(name) LIKE %s OR LOWER(COALESCE(genre, \'\')) LIKE %s'
        params = [f'%{search.lower()}%', f'%{search.lower()}%']
    sql += ' ORDER BY name ASC'

    with connection.cursor() as c:
        c.execute(sql, params)
        columns = [col[0] for col in c.description]
        return [dict(zip(columns, row)) for row in c.fetchall()]


def get_artist_by_id(artist_id: str) -> dict | None:
    with connection.cursor() as c:
        c.execute(
            'SELECT artist_id, name, genre FROM ARTIST WHERE artist_id = %s',
            [artist_id],
        )
        row = c.fetchone()
    if not row:
        return None
    return {'artist_id': row[0], 'name': row[1], 'genre': row[2]}


def get_artist_stats() -> dict:
    """Return stats: total artists, total unique genres, count on events."""
    with connection.cursor() as c:
        c.execute('SELECT COUNT(*) FROM ARTIST')
        total = c.fetchone()[0]

        c.execute('SELECT COUNT(DISTINCT genre) FROM ARTIST WHERE genre IS NOT NULL AND genre != \'\'')
        total_genres = c.fetchone()[0]

        c.execute('SELECT COUNT(DISTINCT artist_id) FROM EVENT_ARTIST')
        on_event = c.fetchone()[0]

    return {
        'total_artists': total,
        'total_genres': total_genres,
        'total_event_artists': on_event,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Create
# ═══════════════════════════════════════════════════════════════════════════════

def create_artist(name: str, genre: str | None) -> str:
    """Insert a new artist. Returns artist_id."""
    artist_id = str(uuid.uuid4())
    with connection.cursor() as c:
        c.execute(
            'INSERT INTO ARTIST (artist_id, name, genre) VALUES (%s, %s, %s)',
            [artist_id, name, genre or None],
        )
    return artist_id


# ═══════════════════════════════════════════════════════════════════════════════
# Update
# ═══════════════════════════════════════════════════════════════════════════════

def update_artist(artist_id: str, name: str, genre: str | None) -> None:
    with connection.cursor() as c:
        c.execute(
            'UPDATE ARTIST SET name = %s, genre = %s WHERE artist_id = %s',
            [name, genre or None, artist_id],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Delete
# ═══════════════════════════════════════════════════════════════════════════════

def delete_artist(artist_id: str) -> None:
    """Delete artist. EVENT_ARTIST rows must be removed first (FK constraint)."""
    with connection.cursor() as c:
        c.execute('DELETE FROM EVENT_ARTIST WHERE artist_id = %s', [artist_id])
        c.execute('DELETE FROM ARTIST WHERE artist_id = %s', [artist_id])
