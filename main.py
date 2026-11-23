"""Link Shortener — starter app for Week 4.

A deliberately tiny FastAPI service you will make *agent-native*. Run it, read it,
then use your coding agent (Antigravity by default) plus the tasks in docs/TASKS.md.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload
Test:
    pytest
"""

import re
import sqlite3
import string
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

DB_PATH = Path(__file__).parent / "links.db"
ALPHABET = string.ascii_letters + string.digits

app = FastAPI(title="Link Shortener")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_db()) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS links (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                url  TEXT NOT NULL
            )"""
        )
        _ensure_clicks_column(conn)
        conn.commit()


def _ensure_clicks_column(conn: sqlite3.Connection) -> None:
    """Add the clicks column to databases created before it existed (idempotent)."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(links)")}
    if "clicks" not in columns:
        conn.execute("ALTER TABLE links ADD COLUMN clicks INTEGER NOT NULL DEFAULT 0")


init_db()


def encode(n: int) -> str:
    """Base62-encode a row id into a short code."""
    base = len(ALPHABET)
    if n == 0:
        return ALPHABET[0]
    chars = []
    while n > 0:
        n, r = divmod(n, base)
        chars.append(ALPHABET[r])
    return "".join(reversed(chars))


ALIAS_RE = re.compile(r"[A-Za-z0-9_-]{1,32}")
# Paths served by other routes; an alias with these names could never redirect.
RESERVED_ALIASES = {"docs", "redoc", "openapi.json", "stats", "shorten"}


class ShortenRequest(BaseModel):
    url: str
    alias: str | None = None


def _validate_alias(alias: str) -> None:
    if not ALIAS_RE.fullmatch(alias):
        raise HTTPException(
            status_code=400, detail="alias must be 1-32 characters of A-Z, a-z, 0-9, _ or -"
        )
    if alias in RESERVED_ALIASES:
        raise HTTPException(status_code=400, detail="alias is reserved")


def _insert_auto_code(conn: sqlite3.Connection, url: str) -> str:
    """Insert a link with a base62 code, skipping ids whose code is already an alias."""
    while True:
        row_id = conn.execute("INSERT INTO links (url) VALUES (?)", (url,)).lastrowid
        code = encode(row_id)
        try:
            conn.execute("UPDATE links SET code = ? WHERE id = ?", (code, row_id))
            return code
        except sqlite3.IntegrityError:
            # Code taken by an alias: drop the placeholder; AUTOINCREMENT never reuses ids.
            conn.execute("DELETE FROM links WHERE id = ?", (row_id,))


@app.post("/shorten")
def shorten(req: ShortenRequest):
    if not req.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="url must start with http:// or https://")
    if req.alias is not None:
        _validate_alias(req.alias)
    with closing(get_db()) as conn:
        if req.alias is None:
            code = _insert_auto_code(conn, req.url)
        else:
            try:
                conn.execute("INSERT INTO links (code, url) VALUES (?, ?)", (req.alias, req.url))
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=409, detail="alias already in use") from None
            code = req.alias
        conn.commit()
    return {"code": code, "short_url": f"/{code}"}


@app.get("/stats/{code}")
def stats(code: str) -> dict:
    with closing(get_db()) as conn:
        row = conn.execute("SELECT url, clicks FROM links WHERE code = ?", (code,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="unknown code")
    return {"url": row["url"], "clicks": row["clicks"]}


@app.get("/{code}")
def redirect(code: str):
    with closing(get_db()) as conn:
        conn.execute("UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,))
        row = conn.execute("SELECT url FROM links WHERE code = ?", (code,)).fetchone()
        if row is not None:
            conn.commit()
    if row is None:
        raise HTTPException(status_code=404, detail="unknown code")
    return RedirectResponse(url=row["url"], status_code=307)
