import datetime
import importlib
import sys
from pathlib import Path
from sqlalchemy import text

def test_insert_connection(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    db_utils = importlib.import_module("db_utils")
    importlib.reload(db_utils)

    for i in range(10):
        db_utils.insert_connection(f"10.0.0.{i}", 2222, datetime.datetime.utcnow())

    with db_utils.engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM connections")).scalar()

    assert count == 10
