import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

TOPICS = [
    ('select', 'Spalten auswählen'), ('where', 'Filtern mit WHERE'),
    ('null', 'Fehlende Werte'), ('distinct', 'Duplikate vermeiden'),
    ('order', 'Ergebnisse sortieren'), ('inner', 'INNER JOIN'), ('left', 'LEFT JOIN'),
]


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'tutor.sqlite'
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS records (
              kind TEXT NOT NULL, id TEXT PRIMARY KEY, body TEXT NOT NULL,
              created TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS records_kind ON records(kind);
            ''')

    @contextmanager
    def db(self):
        with sqlite3.connect(self.path, timeout=20) as db:
            db.row_factory = sqlite3.Row
            yield db

    def put(self, kind, body, id=None):
        id = id or str(uuid4())
        body = {**body, 'id': id}
        with self.db() as db:
            db.execute('INSERT INTO records VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                       (kind, id, json.dumps(body, ensure_ascii=False), datetime.now(timezone.utc).isoformat()))
        return body

    def get(self, kind, id):
        with self.db() as db:
            row = db.execute('SELECT body FROM records WHERE kind=? AND id=?', (kind, id)).fetchone()
        if not row:
            raise KeyError(id)
        return json.loads(row['body'])

    def list(self, kind):
        with self.db() as db:
            rows = db.execute('SELECT body FROM records WHERE kind=? ORDER BY created, id', (kind,)).fetchall()
        return [json.loads(row['body']) for row in rows]

    def allowed(self):
        return [r['name'] for r in self.list('table') if r['allowed']]

    def progress(self):
        attempts = self.list('attempt')
        result = []
        for id, title in TOPICS:
            relevant = [a for a in attempts if a['topic'] == id]
            correct = [a for a in relevant if a['result']['verdict'] == 'correct']
            independent = {a.get('lineage', a['exercise_id']) for a in correct if not a['supported']}
            state = ('consolidated' if len(independent) >= 2 else 'independent' if independent
                     else 'supported' if correct else 'started' if relevant else 'new')
            result.append(dict(id=id, title=title, state=state, independent=len(independent),
                               attempts=len(relevant)))
        return result
