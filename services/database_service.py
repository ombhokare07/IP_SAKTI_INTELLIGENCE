"""Local SQLite persistence with transactions and bound SQL parameters."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from intelligence.contracts import now_iso

class DatabaseService:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS artifacts (kind TEXT NOT NULL, id TEXT NOT NULL, created_at TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(kind,id))')
            db.execute(
                '''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    google_sub TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    name TEXT NOT NULL DEFAULT '',
                    picture TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login_at TEXT NOT NULL
                )'''
            )
            self._migrate_artifact_users(db)
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

    @staticmethod
    def _user_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    @staticmethod
    def _migrate_artifact_users(db: sqlite3.Connection) -> None:
        """Copy legacy user artifacts into the constrained user table once."""
        rows = db.execute("SELECT data FROM artifacts WHERE kind='user'").fetchall()
        for row in rows:
            try:
                record = json.loads(row['data'])
                google_sub = record['google_sub']
                email = record['email']
                if not isinstance(google_sub, str) or not google_sub or not isinstance(email, str) or not email:
                    continue
                created_at = record.get('created_at') or now_iso()
                updated_at = record.get('updated_at') or record.get('last_login_at') or created_at
                last_login_at = record.get('last_login_at') or updated_at
                db.execute(
                    '''INSERT OR IGNORE INTO users
                       (google_sub,email,name,picture,created_at,updated_at,last_login_at)
                       VALUES(?,?,?,?,?,?,?)''',
                    (google_sub,email,record.get('name') or '',record.get('picture') or '',created_at,updated_at,last_login_at),
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue

    def get_user_by_google_sub(self, google_sub: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute('SELECT * FROM users WHERE google_sub=?',(google_sub,)).fetchone()
        return self._user_dict(row)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute('SELECT * FROM users WHERE email=? COLLATE NOCASE',(email,)).fetchone()
        return self._user_dict(row)

    def create_user(self, google_sub: str, email: str, name: str, picture: str, timestamp: str) -> dict[str, Any]:
        """Create one Google-backed user while enforcing subject and email uniqueness."""
        try:
            with self.connect() as db:
                cursor = db.execute(
                    '''INSERT INTO users
                       (google_sub,email,name,picture,created_at,updated_at,last_login_at)
                       VALUES(?,?,?,?,?,?,?)''',
                    (google_sub,email,name,picture,timestamp,timestamp,timestamp),
                )
                user_id = cursor.lastrowid
                row = db.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
        except sqlite3.IntegrityError as exc:
            raise ValueError('A user with this Google identity or email already exists.') from exc
        user = self._user_dict(row)
        assert user is not None
        self.put('user',google_sub,user)
        return user

    def update_user_login(self, google_sub: str, email: str, name: str, picture: str, timestamp: str) -> dict[str, Any]:
        """Refresh verified profile claims and record the successful login time."""
        try:
            with self.connect() as db:
                cursor = db.execute(
                    '''UPDATE users SET email=?,name=?,picture=?,updated_at=?,last_login_at=?
                       WHERE google_sub=?''',
                    (email,name,picture,timestamp,timestamp,google_sub),
                )
                if cursor.rowcount != 1:
                    raise KeyError(google_sub)
                row = db.execute('SELECT * FROM users WHERE google_sub=?',(google_sub,)).fetchone()
        except sqlite3.IntegrityError as exc:
            raise ValueError('This verified email belongs to another account.') from exc
        user = self._user_dict(row)
        assert user is not None
        self.put('user',google_sub,user)
        return user
