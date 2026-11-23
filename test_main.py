import sqlite3
from contextlib import closing

from fastapi.testclient import TestClient

import main
from main import app

client = TestClient(app)


def test_shorten_and_redirect():
    r = client.post("/shorten", json={"url": "https://example.com"})
    assert r.status_code == 200
    code = r.json()["code"]
    assert code
    r2 = client.get(f"/{code}", follow_redirects=False)
    assert r2.status_code == 307
    assert r2.headers["location"] == "https://example.com"


def test_rejects_bad_url():
    r = client.post("/shorten", json={"url": "ftp://nope"})
    assert r.status_code == 400


def test_unknown_code_404():
    r = client.get("/does-not-exist", follow_redirects=False)
    assert r.status_code == 404


def _shorten(url: str) -> str:
    r = client.post("/shorten", json={"url": url})
    assert r.status_code == 200
    return r.json()["code"]


def test_stats_new_link_has_zero_clicks():
    code = _shorten("https://example.com/stats-zero")
    r = client.get(f"/stats/{code}")
    assert r.status_code == 200
    assert r.json() == {"url": "https://example.com/stats-zero", "clicks": 0}


def test_redirect_increments_clicks():
    code = _shorten("https://example.com/stats-three")
    for _ in range(3):
        assert client.get(f"/{code}", follow_redirects=False).status_code == 307
    r = client.get(f"/stats/{code}")
    assert r.status_code == 200
    assert r.json()["clicks"] == 3


def test_stats_does_not_increment_clicks():
    code = _shorten("https://example.com/stats-readonly")
    client.get(f"/stats/{code}")
    r = client.get(f"/stats/{code}")
    assert r.status_code == 200
    assert r.json()["clicks"] == 0


def test_stats_unknown_code_404():
    r = client.get("/stats/does-not-exist")
    assert r.status_code == 404
    assert r.json() == {"detail": "unknown code"}


def test_redirect_shape_unchanged_with_counter():
    r = client.post("/shorten", json={"url": "https://example.com/shape"})
    assert r.status_code == 200
    assert set(r.json().keys()) == {"code", "short_url"}
    code = r.json()["code"]
    r2 = client.get(f"/{code}", follow_redirects=False)
    assert r2.status_code == 307
    assert r2.headers["location"] == "https://example.com/shape"


def test_migration_adds_clicks_to_legacy_db(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy.db"
    with closing(sqlite3.connect(legacy)) as conn:
        conn.execute(
            """CREATE TABLE links (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                url  TEXT NOT NULL
            )"""
        )
        conn.execute("INSERT INTO links (code, url) VALUES (?, ?)", ("old", "https://old.example"))
        conn.commit()
    monkeypatch.setattr(main, "DB_PATH", legacy)
    main.init_db()
    main.init_db()
    with closing(sqlite3.connect(legacy)) as conn:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(links)")]
        row = conn.execute("SELECT url, clicks FROM links WHERE code = ?", ("old",)).fetchone()
    assert "clicks" in columns
    assert row == ("https://old.example", 0)
