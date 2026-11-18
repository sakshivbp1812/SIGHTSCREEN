import pytest
from fastapi.testclient import TestClient
from app import data, db, model


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    model.load.cache_clear()
    data.seed()
    from app import main
    main._hits.clear()
    main._eval_hits.clear()
    app = main.app
    return TestClient(app)
