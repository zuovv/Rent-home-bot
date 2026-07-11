"""
Ijara elonlari boti uchun ma'lumotlar bazasi (SQLite).
Barcha jadval va so'rovlar shu yerda.
"""
import os
import sqlite3
from contextlib import contextmanager

# Railway'da doimiy Volume qo'shsangiz, uni masalan /data ga bog'lab,
# DB_PATH environment o'zgaruvchisini /data/ijara_bot.db qiling.
DB_PATH = os.environ.get("DB_PATH", "ijara_bot.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                owner_username TEXT,
                tuman TEXT NOT NULL,
                xona_soni TEXT NOT NULL,
                narx INTEGER NOT NULL,
                kim_uchun TEXT NOT NULL,
                tavsif TEXT,
                telefon TEXT NOT NULL,
                photo_file_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_listing(owner_id, owner_username, tuman, xona_soni, narx, kim_uchun, tavsif, telefon, photo_file_id):
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO listings
                (owner_id, owner_username, tuman, xona_soni, narx, kim_uchun, tavsif, telefon, photo_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (owner_id, owner_username, tuman, xona_soni, narx, kim_uchun, tavsif, telefon, photo_file_id))
        return cur.lastrowid


def search_listings(tuman=None, xona_soni=None, kim_uchun=None, max_narx=None, limit=10, offset=0):
    query = "SELECT * FROM listings WHERE is_active = 1"
    params = []
    if tuman and tuman != "Barchasi":
        query += " AND tuman = ?"
        params.append(tuman)
    if xona_soni and xona_soni != "Barchasi":
        query += " AND xona_soni = ?"
        params.append(xona_soni)
    if kim_uchun and kim_uchun != "Barchasi":
        query += " AND (kim_uchun = ? OR kim_uchun = 'Barchasi uchun')"
        params.append(kim_uchun)
    if max_narx:
        query += " AND narx <= ?"
        params.append(max_narx)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def count_listings(tuman=None, xona_soni=None, kim_uchun=None, max_narx=None):
    query = "SELECT COUNT(*) as cnt FROM listings WHERE is_active = 1"
    params = []
    if tuman and tuman != "Barchasi":
        query += " AND tuman = ?"
        params.append(tuman)
    if xona_soni and xona_soni != "Barchasi":
        query += " AND xona_soni = ?"
        params.append(xona_soni)
    if kim_uchun and kim_uchun != "Barchasi":
        query += " AND (kim_uchun = ? OR kim_uchun = 'Barchasi uchun')"
        params.append(kim_uchun)
    if max_narx:
        query += " AND narx <= ?"
        params.append(max_narx)
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()["cnt"]


def get_user_listings(owner_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM listings WHERE owner_id = ? ORDER BY created_at DESC", (owner_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_listing(listing_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
        return dict(row) if row else None


def deactivate_listing(listing_id, owner_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE listings SET is_active = 0 WHERE id = ? AND owner_id = ?",
            (listing_id, owner_id),
        )
