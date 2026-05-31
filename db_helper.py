"""
RTConnect - Database Helper
Unified interface untuk SQLite (lokal) dan PostgreSQL (production)

Semua route tetap menggunakan pola lama:
  db = get_db()
  row = db.execute("SELECT ...", (val,)).fetchone()
  rows = db.execute("SELECT ...", (val,)).fetchall()
  db.execute("INSERT ...", (val,))
  db.commit()
  db.close()

Helper ini membungkus kedua engine agar sintaks tetap sama.
"""
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "")


class CursorWrapper:
    """Membungkus psycopg2 cursor agar .fetchone() dan .fetchall() return dict."""
    def __init__(self, cursor):
        self._cur = cursor

    @property
    def lastrowid(self):
        # PostgreSQL: pakai RETURNING id
        try:
            row = self._cur.fetchone()
            if row:
                return row[0]
        except Exception:
            pass
        return None

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in self._cur.description]
        return dict(zip(cols, row))

    def fetchall(self):
        rows = self._cur.fetchall()
        if not rows:
            return []
        cols = [d[0] for d in self._cur.description]
        return [dict(zip(cols, r)) for r in rows]


class ConnectionWrapper:
    """Membungkus koneksi PostgreSQL agar mirip SQLite."""
    def __init__(self, conn):
        self._conn = conn
        self._cursor = conn.cursor()

    def execute(self, sql, params=()):
        # Konversi ? ke %s untuk PostgreSQL
        pg_sql = sql.replace("?", "%s")
        # Handle INSERT ... RETURNING untuk lastrowid
        if pg_sql.strip().upper().startswith("INSERT"):
            # Tambah RETURNING id jika belum ada
            if "RETURNING" not in pg_sql.upper():
                pg_sql = pg_sql.rstrip().rstrip(";") + " RETURNING id"
        self._cursor.execute(pg_sql, params)
        return CursorWrapper(self._cursor)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._cursor.close()
        self._conn.close()


def get_db():
    if DATABASE_URL:
        import psycopg2
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        return ConnectionWrapper(conn)
    else:
        import sqlite3
        DB_PATH = os.environ.get("DB_PATH", "rtconnect.db")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        # Patch fetchone/fetchall to return dict
        original_execute = conn.execute
        def execute_wrapper(sql, params=()):
            cur = original_execute(sql, params)
            original_fetchone = cur.fetchone
            original_fetchall = cur.fetchall
            def fetchone():
                row = original_fetchone()
                return dict(row) if row else None
            def fetchall():
                rows = original_fetchall()
                return [dict(r) for r in rows]
            cur.fetchone = fetchone
            cur.fetchall = fetchall
            return cur
        conn.execute = execute_wrapper
        return conn
