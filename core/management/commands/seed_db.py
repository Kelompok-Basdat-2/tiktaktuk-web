"""
Django management command to seed the database using raw SQL from seed_data.sql.

Usage:
    python manage.py seed_db

Runs the full dump: DROP, CREATE, INSERT — all inside a single transaction.
Comment-only blocks are filtered out. Idempotent: IF NOT EXISTS / DROP IF EXISTS.
"""

import os

import sqlparse
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Seed the database with raw SQL from seed_data.sql'

    def handle(self, *_args, **_options):
        dump_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'seed_data.sql',
        )

        if not os.path.exists(dump_path):
            raise CommandError(f'Seed data not found at: {dump_path}')

        with open(dump_path, 'r', encoding='utf-8') as f:
            raw_sql = f.read()

        statements = sqlparse.split(raw_sql)

        total = 0
        skipped = 0
        errors = 0

        with transaction.atomic():
            with connection.cursor() as cursor:
                for stmt in statements:
                    # Filter out comment-only / whitespace-only blocks
                    body = sqlparse.format(stmt, strip_comments=True).strip()
                    if not body:
                        skipped += 1
                        continue

                    try:
                        cursor.execute(stmt)
                        total += 1
                    except Exception as e:
                        errors += 1
                        self.stderr.write(
                            self.style.ERROR(f'Failed: {str(e)[:120]}')
                        )
                        self.stderr.write(
                            f'  SQL: {stmt[:200].replace(chr(10), " ")}...'
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete: {total} executed, {skipped} skipped, '
                f'{errors} errors'
            )
        )
