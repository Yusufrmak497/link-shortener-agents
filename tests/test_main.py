import sqlite3
from contextlib import closing

import pytest
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


def _shorten_alias(url: str, alias: str):
    return client.post("/shorten", json={"url": url, "alias": alias})


def test_shorten_with_alias_uses_alias_as_code():
    r = _shorten_alias("https://example.com/alias", "my-link")
    assert r.status_code == 200
    assert r.json() == {"code": "my-link", "short_url": "/my-link"}
    r2 = client.get("/my-link", follow_redirects=False)
    assert r2.status_code == 307
    assert r2.headers["location"] == "https://example.com/alias"


def test_alias_already_taken_returns_409():
    assert _shorten_alias("https://first.example", "taken").status_code == 200
    r = _shorten_alias("https://second.example", "taken")
    assert r.status_code == 409
    assert r.json() == {"detail": "alias already in use"}
    r2 = client.get("/taken", follow_redirects=False)
    assert r2.headers["location"] == "https://first.example"


def test_alias_matching_generated_code_returns_409():
    code = _shorten("https://auto.example")
    r = _shorten_alias("https://other.example", code)
    assert r.status_code == 409
    r2 = client.get(f"/{code}", follow_redirects=False)
    assert r2.headers["location"] == "https://auto.example"


def test_generated_code_skips_taken_alias():
    # Aliases use row ids 1-2; the next auto ids 3 and 4 encode to "d" and "e".
    for alias in ("d", "e"):
        assert _shorten_alias(f"https://alias-{alias}.example", alias).status_code == 200
    r = client.post("/shorten", json={"url": "https://auto.example"})
    assert r.status_code == 200
    code = r.json()["code"]
    assert code not in {"d", "e"}
    r2 = client.get(f"/{code}", follow_redirects=False)
    assert r2.headers["location"] == "https://auto.example"
    for alias in ("d", "e"):
        r3 = client.get(f"/{alias}", follow_redirects=False)
        assert r3.headers["location"] == f"https://alias-{alias}.example"


@pytest.mark.parametrize("alias", ["", "has space", "a/b", "x" * 33, "dot.ted", "ünï"])
def test_invalid_alias_returns_400(alias):
    r = _shorten_alias("https://example.com", alias)
    assert r.status_code == 400


def test_alias_of_max_length_is_accepted():
    assert _shorten_alias("https://example.com/long", "x" * 32).status_code == 200


@pytest.mark.parametrize("alias", ["docs", "redoc", "openapi.json", "stats", "shorten"])
def test_reserved_alias_returns_400(alias):
    r = _shorten_alias("https://example.com", alias)
    assert r.status_code == 400


def test_bad_url_with_alias_returns_400_and_alias_stays_free():
    assert _shorten_alias("javascript:alert(1)", "free").status_code == 400
    assert client.get("/free", follow_redirects=False).status_code == 404
    assert _shorten_alias("https://example.com/free", "free").status_code == 200


def test_alias_response_shape_unchanged():
    r = _shorten_alias("https://example.com/shape-alias", "shape")
    assert r.status_code == 200
    assert set(r.json().keys()) == {"code", "short_url"}


def test_null_alias_behaves_like_no_alias():
    r = client.post("/shorten", json={"url": "https://example.com/null", "alias": None})
    assert r.status_code == 200
    assert r.json()["code"]
