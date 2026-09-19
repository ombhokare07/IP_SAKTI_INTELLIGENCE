"""Local SQLite persistence with transactions and bound SQL parameters."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from intelligence.contracts import now_iso

class DatabaseService:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS artifacts (kind TEXT NOT NULL, id TEXT NOT NULL, created_at TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(kind,id))')
    @contextmanager
    def connect(self):
        connection=sqlite3.connect(self.path,timeout=20)
        connection.row_factory=sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()
    def put(self,kind,identifier,data,*,immutable=False):
        encoded=json.dumps(data,ensure_ascii=False,sort_keys=True,allow_nan=False)
        with self.connect() as db:
            existing=db.execute('SELECT data FROM artifacts WHERE kind=? AND id=?',(kind,identifier)).fetchone()
            if existing and immutable:
                if existing['data']!=encoded:raise ValueError('An immutable version already exists with different content.')
                return False
            db.execute('INSERT INTO artifacts(kind,id,created_at,data) VALUES(?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET data=excluded.data',(kind,identifier,now_iso(),encoded))
        return True
    def get(self,kind,identifier):
        with self.connect() as db:
            row=db.execute('SELECT data FROM artifacts WHERE kind=? AND id=?',(kind,identifier)).fetchone()
        return json.loads(row['data']) if row else None
    def list(self,kind):
        with self.connect() as db:
            rows=db.execute('SELECT data FROM artifacts WHERE kind=? ORDER BY created_at DESC,id',(kind,)).fetchall()
        return [json.loads(row['data']) for row in rows]
