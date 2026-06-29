"""app.client_pg — Postgres read-only client (audit + source of truth)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, List, Optional

import psycopg
from psycopg.rows import dict_row

from . import config


# TODO: implement ping() -> bool
# Connect to Postgres, run SELECT 1, return True if succeed, False otherwise.
# HINT: use _connect() context manager, then cur.execute("SELECT 1")
def ping() -> bool:
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception:
        return False


# TODO: implement _connect() context manager
# Create a psycopg connection using config.DATABASE_URL with connect_timeout=5
# Yield the connection, close in finally.
# HINT: use @contextmanager decorator
@contextmanager
def _connect() -> Iterator[psycopg.Connection]:
    conn = None
    try:
        conn = psycopg.connect(config.DATABASE_URL, connect_timeout=5)
        yield conn
    finally:
        if conn is not None:
            conn.close()


# TODO: implement fetch_corpus_hits(ids: List[str]) -> List[dict]
# Given a list of UUIDs (as strings), fetch the corresponding rows from
# the core.encoder_corpus table. Return rows in the same order as ids.
# HINT: SELECT id::text AS id, text, primary_label, labels, lang, source
# HINT: FROM core.encoder_corpus WHERE id = ANY(%s::uuid[])
# HINT: use psycopg.rows.dict_row for row factory
def fetch_corpus_hits(ids: List[str]) -> List[dict]:
    if not ids:
        return []
        
    try:
        with _connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT id::text AS id, text, primary_label, labels, lang, source FROM core.encoder_corpus WHERE id = ANY(%s::uuid[])",
                    (ids,)
                )
                rows = cur.fetchall()
                
        # برای حفظ ترتیب دقیق هماهنگ با ورودی ids
        row_map = {row["id"]: row for row in rows}
        return [row_map[id_str] for id_str in ids if id_str in row_map]
    except Exception:
        return []


# TODO: (bonus) implement count_corpus() -> Optional[int]
# SELECT count(*) FROM core.encoder_corpus
def count_corpus() -> Optional[int]:
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM core.encoder_corpus")
                res = cur.fetchone()
                return res[0] if res else None
    except Exception:
        return None