"""
Authentication utilities — all raw SQL, zero ORM.

Password hashing uses Django's PBKDF2 hasher (make_password / check_password)
which is a pure utility — no ORM involved. All database operations use
connection.cursor() with parameterized queries.
"""

from django.contrib.auth.hashers import make_password, check_password
from django.db import connection


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """PBKDF2 hash for storage in USER_ACCOUNT.password."""
    return make_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """Check a plaintext password against a stored hash."""
    return check_password(password, hashed)


# ── User lookup ───────────────────────────────────────────────────────────────

def get_user_by_username(username: str) -> dict | None:
    with connection.cursor() as c:
        c.execute(
            'SELECT user_id, username, password FROM USER_ACCOUNT WHERE username = %s',
            [username],
        )
        row = c.fetchone()
    if row:
        return {'user_id': row[0], 'username': row[1], 'password': row[2]}
    return None


def get_user_by_id(user_id: str) -> dict | None:
    with connection.cursor() as c:
        c.execute(
            'SELECT user_id, username FROM USER_ACCOUNT WHERE user_id = %s',
            [user_id],
        )
        row = c.fetchone()
    if row:
        return {'user_id': row[0], 'username': row[1]}
    return None


# ── Roles ─────────────────────────────────────────────────────────────────────

ROLE_MAP = {'administrator': 'admin', 'organizer': 'organizer', 'customer': 'customer'}


def get_user_roles(user_id: str) -> list[str]:
    """Return list of role_name values (e.g. ['administrator', 'organizer'])."""
    with connection.cursor() as c:
        c.execute(
            '''SELECT r.role_name FROM ROLE r
               JOIN ACCOUNT_ROLE ar ON r.role_id = ar.role_id
               WHERE ar.user_id = %s''',
            [user_id],
        )
        return [row[0] for row in c.fetchall()]


def get_primary_role(user_id: str) -> str | None:
    """Return 'admin' | 'organizer' | 'customer' | None."""
    roles = get_user_roles(user_id)
    for db_role, short in ROLE_MAP.items():
        if db_role in roles:
            return short
    return None


# ── Profiles ──────────────────────────────────────────────────────────────────

def get_customer_profile(user_id: str) -> dict | None:
    with connection.cursor() as c:
        c.execute(
            'SELECT customer_id, full_name, phone_number FROM CUSTOMER WHERE user_id = %s',
            [user_id],
        )
        row = c.fetchone()
    if row:
        return {'customer_id': row[0], 'full_name': row[1], 'phone_number': row[2]}
    return None


def get_organizer_profile(user_id: str) -> dict | None:
    with connection.cursor() as c:
        c.execute(
            'SELECT organizer_id, organizer_name, contact_email FROM ORGANIZER WHERE user_id = %s',
            [user_id],
        )
        row = c.fetchone()
    if row:
        return {'organizer_id': row[0], 'organizer_name': row[1], 'contact_email': row[2]}
    return None


# ── User creation ─────────────────────────────────────────────────────────────

def _next_id(table: str, prefix: str) -> str:
    with connection.cursor() as c:
        c.execute(f'SELECT COUNT(*) FROM {table}')
        count = c.fetchone()[0]
    return f'{prefix}{count + 1:03d}'


def create_user(username: str, password: str, role_name: str) -> str | None:
    """
    Insert into USER_ACCOUNT + ACCOUNT_ROLE.
    Returns user_id or None on failure.
    """
    user_id = _next_id('USER_ACCOUNT', 'u-')
    hashed = hash_password(password)

    with connection.cursor() as c:
        c.execute('SELECT role_id FROM ROLE WHERE role_name = %s', [role_name])
        row = c.fetchone()
        if not row:
            return None
        role_id = row[0]

        c.execute(
            'INSERT INTO USER_ACCOUNT (user_id, username, password) VALUES (%s, %s, %s)',
            [user_id, username, hashed],
        )
        c.execute(
            'INSERT INTO ACCOUNT_ROLE (role_id, user_id) VALUES (%s, %s)',
            [role_id, user_id],
        )
    return user_id


def create_customer_profile(user_id: str, full_name: str, phone: str) -> str:
    """Create CUSTOMER row. Returns customer_id."""
    cust_id = _next_id('CUSTOMER', 'cust-')
    with connection.cursor() as c:
        c.execute(
            'INSERT INTO CUSTOMER (customer_id, full_name, phone_number, user_id) VALUES (%s, %s, %s, %s)',
            [cust_id, full_name, phone, user_id],
        )
    return cust_id


def create_organizer_profile(
    user_id: str, organizer_name: str, email: str, phone: str
) -> str:
    """Create ORGANIZER row. Returns organizer_id."""
    org_id = _next_id('ORGANIZER', 'org-')
    with connection.cursor() as c:
        c.execute(
            '''INSERT INTO ORGANIZER (organizer_id, organizer_name, contact_email, user_id)
               VALUES (%s, %s, %s, %s)''',
            [org_id, organizer_name, email, user_id],
        )
    return org_id
