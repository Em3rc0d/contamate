"""Persistencia local. Cada query de negocio se restringe al id de empresa/RUC."""
import os
import sqlite3
from pathlib import Path

DDL = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY,
    ruc TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS allowed_roots (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    UNIQUE(company_id, path)
);
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, path)
);
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    source_kind TEXT NOT NULL CHECK(source_kind IN ('xml','registro')),
    issuer_ruc TEXT NOT NULL,
    receiver_ruc TEXT NOT NULL DEFAULT '',
    voucher_id TEXT NOT NULL,
    voucher_type TEXT NOT NULL DEFAULT '01',
    issue_date TEXT NOT NULL,
    currency TEXT NOT NULL,
    total TEXT NOT NULL,
    source_location TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_company ON records(company_id,issue_date,source_kind);
CREATE INDEX IF NOT EXISTS idx_records_key ON records(company_id,issuer_ruc,voucher_id);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    due_date TEXT,
    done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0,1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def home() -> Path:
    return Path(os.getenv('CONTAMATE_HOME', str(Path.home() / '.contamate'))).expanduser().resolve()


def connect() -> sqlite3.Connection:
    base = home()
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    p = base / 'contamate.sqlite3'
    conn = sqlite3.connect(p, timeout=20)
    conn.execute('PRAGMA busy_timeout=20000;')
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.row_factory = sqlite3.Row
    conn.executescript(DDL)
    try:
        conn.executescript(KNOWLEDGE_DDL)
    except sqlite3.OperationalError as exc:
        raise RuntimeError("SQLite sin extensión FTS5; instalación de Python incompatible") from exc
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    return conn


def company(conn: sqlite3.Connection, ruc: str) -> sqlite3.Row:
    row = conn.execute('SELECT * FROM companies WHERE ruc = ?', (ruc,)).fetchone()
    if row is None:
        raise ValueError(f'RUC no registrado: {ruc}')
    return row


def check_ruc(ruc: str):
    if len(ruc) != 11 or not ruc.isascii() or not ruc.isdigit():
        raise ValueError('El RUC debe contener exactamente 11 dígitos ASCII.')


def add_company(conn, ruc, name):
    check_ruc(ruc)
    if not name.strip():
        raise ValueError('La razón social no puede quedar vacía.')
    with conn:
        conn.execute('INSERT INTO companies(ruc,name) VALUES(?,?)', (ruc, name.strip()))


def add_root(conn, ruc: str, folder: str):
    c = company(conn, ruc)
    p = Path(folder).expanduser().resolve(strict=True)
    if not p.is_dir():
        raise ValueError('La ruta autorizada debe ser una carpeta existente.')
    # Proteger aislamiento documental también si el operador usa CLI.
    for row in conn.execute('SELECT company_id,path FROM allowed_roots WHERE company_id<>?',(c['id'],)):
        other = Path(row['path']).resolve()
        if p == other or p.is_relative_to(other) or other.is_relative_to(p):
            raise ValueError('La carpeta coincide o se solapa con el expediente de otra empresa.')
    with conn:
        conn.execute('INSERT OR IGNORE INTO allowed_roots(company_id,path) VALUES(?,?)', (c['id'], str(p)))


def roots(conn, company_id):
    return [Path(x['path']) for x in conn.execute('SELECT path FROM allowed_roots WHERE company_id=?', (company_id,))]


def list_tasks(conn, company_id):
    return [dict(x) for x in conn.execute('SELECT * FROM tasks WHERE company_id=? ORDER BY done,due_date,id', (company_id,))]

KNOWLEDGE_DDL = """
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    local_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    effective_from TEXT,
    effective_until TEXT,
    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_chunks USING fts5(
    body, source_id UNINDEXED, page UNINDEXED, tokenize='unicode61 remove_diacritics 2'
);
"""
