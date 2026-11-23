import pytest

import main


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Give every test its own SQLite file so tests never share state or touch links.db."""
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "links.db")
    main.init_db()
