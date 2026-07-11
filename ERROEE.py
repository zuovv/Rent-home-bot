"""
Ijara elonlari boti uchun ma'lumotlar bazasi (SQLite).
Barcha jadval va so'rovlar shu yerda.
"""
import os
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

# Railway'da Volume qo'shsangiz, uni /data ga bog'lab,
# DB_PATH environment o'zgaruvchisini /data/ijara_bot.db qiling.
DB_PATH = os.environ.get("DB_PATH", "ijara_bot.db")

EXPIRY_DAYS = 20


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
                contact_username TEXT,
                manzil_text TEXT,
                latitude REAL,
                longitude REAL,
                photo_file_ids TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Eski (Volume'dagi) bazada yo'q bo'lgan ustunlarni qo'shib qo'yamiz.
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(listings)").fetchall()}
        needed_cols = {
            "contact_username": "TEXT",
            "manzil_text": "TEXT",
            "latitude": "REAL",
            "longitude": "REAL",
            "photo_file_ids": "TEXT",
        }
        for col, coltype in needed_cols.items():
            if col not in existing_cols:
                conn.execute(f"ALTER TABLE listings ADD COLUMN {col} {coltype}")


def add_listing(owner_id, owner_username, tuman, xona_soni, narx, kim_uchun, tavsif,
                 telefon, contact_username, manzil_text, latitude, longitude, photo_file_ids):
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO listings
                (owner_id, owner_username, tuman, xona_soni, narx, kim_uchun, tavsif,
                 telefon, contact_username, manzil_text, latitude, longitude, photo_file_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (owner_id, owner_username, tuman, xona_soni, narx, kim_uchun, tavsif,
              telefon, contact_username, manzil_text, latitude, longitude,
              json.dumps(photo_file_ids or [])))
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
        query += " AND kim_uchun = ?"
        params.append(kim_uchun)
    if max_narx:
        query += " AND narx <= ?"
        params.append(max_narx)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(query, params).fetchall()]
        for r in rows:
            r["photo_file_ids"] = json.loads(r["photo_file_ids"] or "[]")
        return rows


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
        query += " AND kim_uchun = ?"
        params.append(kim_uchun)
    if max_narx:
        query += " AND narx <= ?"
        params.append(max_narx)
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()["cnt"]


def get_user_listings(owner_id):
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM listings WHERE owner_id = ? ORDER BY created_at DESC", (owner_id,)
        ).fetchall()]
        for r in rows:
            r["photo_file_ids"] = json.loads(r["photo_file_ids"] or "[]")
        return rows


def get_listing(listing_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["photo_file_ids"] = json.loads(d["photo_file_ids"] or "[]")
        return d


def deactivate_listing(listing_id, owner_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE listings SET is_active = 0 WHERE id = ? AND owner_id = ?",
            (listing_id, owner_id),
        )


def deactivate_expired_listings():
    """EXPIRY_DAYS kundan eski faol elonlarni o'chiradi. O'chirilgan elonlar sonini qaytaradi."""
    cutoff = (datetime.utcnow() - timedelta(days=EXPIRY_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE listings SET is_active = 0 WHERE is_active = 1 AND created_at < ?",
            (cutoff,),
        )
        return cur.rowcount
