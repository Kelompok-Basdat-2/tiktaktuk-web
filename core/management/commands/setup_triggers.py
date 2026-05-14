"""
Django management command to install PostgreSQL triggers and stored procedures.

Usage:
    python manage.py setup_triggers

Runs all .sql files matching trigger_*.sql in the commands directory.
Idempotent — uses CREATE OR REPLACE and DROP TRIGGER IF EXISTS.
"""

import os
import glob

import sqlparse
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Install PostgreSQL triggers and stored procedures'

    def handle(self, *_args, **_options):
        cmd_dir = os.path.dirname(os.path.abspath(__file__))
        sql_files = sorted(glob.glob(os.path.join(cmd_dir, 'trigger_*.sql')))

        if not sql_files:
            self.stdout.write(self.style.WARNING('No trigger_*.sql files found.'))
            return

        total_files = 0
        total_stmts = 0
        errors = 0

        for sql_file in sql_files:
            filename = os.path.basename(sql_file)
            self.stdout.write(f'  Installing {filename} ... ', ending='')

            with open(sql_file, 'r', encoding='utf-8') as f:
                raw_sql = f.read()

            statements = sqlparse.split(raw_sql)

            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        for stmt in statements:
                            body = sqlparse.format(
                                stmt, strip_comments=True
                            ).strip()
                            if not body:
                                continue
                            cursor.execute(stmt)
                            total_stmts += 1
                total_files += 1
                self.stdout.write(self.style.SUCCESS('OK'))
            except Exception as e:
                errors += 1
                self.stderr.write(self.style.ERROR(f'FAILED: {e}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Triggers installed: {total_files} files, '
                f'{total_stmts} statements, {errors} errors'
            )
        )
