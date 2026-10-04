# -*- coding: utf-8 -*-
"""SQLite baza: foydalanuvchilar, buyruqlar, statistika."""
import json
import sqlite3
import threading
import time

import config

_lock = threading.RLock()
_conn = None
FIELDS = {"category", "command", "status", "desc_uz", "desc_en", "desc_ru", "desc_ar"}


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def run(sql, args=()):
    with _lock:
        c = conn()
        cur = c.execute(sql, args)
        c.commit()
        return cur.lastrowid


def one(sql, args=()):
    with _lock:
        return conn().execute(sql, args).fetchone()


def many(sql, args=()):
    with _lock:
        return conn().execute(sql, args).fetchall()


def init():
    with _lock:
        c = conn()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, lang TEXT, first_name TEXT,
            username TEXT, joined INTEGER, last_seen INTEGER);
        CREATE TABLE IF NOT EXISTS commands(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL, command TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ok', desc_key TEXT,
            desc_uz TEXT, desc_en TEXT, desc_ru TEXT, desc_ar TEXT);
        CREATE TABLE IF NOT EXISTS stats(name TEXT PRIMARY KEY, value INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        """)
        c.commit()
    seed()


def seed():
    """Birinchi ishga tushishda seed.json dagi buyruqlarni bazaga yuklaydi."""
    if one("SELECT value FROM meta WHERE key='seeded'"):
        return
    with open(config.SEED_PATH, encoding="utf-8") as f:
        items = json.load(f)
    with _lock:
        c = conn()
        c.executemany(
            "INSERT INTO commands(category,command,status,desc_key) VALUES(?,?,?,?)",
            [(i["cat"], i["cmd"], i["st"], i["key"]) for i in items])
        c.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('seeded','1')")
        c.commit()


# ---------- foydalanuvchilar ----------
def upsert_user(u):
    now = int(time.time())
    run("INSERT OR IGNORE INTO users(user_id,first_name,username,joined,last_seen) VALUES(?,?,?,?,?)",
        (u.id, u.first_name, u.username, now, now))
    run("UPDATE users SET first_name=?, username=?, last_seen=? WHERE user_id=?",
        (u.first_name, u.username, now, u.id))


def touch(uid):
    run("UPDATE users SET last_seen=? WHERE user_id=?", (int(time.time()), uid))


def get_lang(uid):
    r = one("SELECT lang FROM users WHERE user_id=?", (uid,))
    return r["lang"] if r and r["lang"] in config.LANGS else None


def set_lang(uid, lang):
    run("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))


def count_users():
    return one("SELECT COUNT(*) c FROM users")["c"]


def joined_since(ts):
    return one("SELECT COUNT(*) c FROM users WHERE joined>=?", (ts,))["c"]


def active_since(ts):
    return one("SELECT COUNT(*) c FROM users WHERE last_seen>=?", (ts,))["c"]


def lang_counts():
    return {r["lang"]: r["c"] for r in many("SELECT lang, COUNT(*) c FROM users WHERE lang IS NOT NULL GROUP BY lang")}


def all_user_ids():
    return [r["user_id"] for r in many("SELECT user_id FROM users")]


# ---------- buyruqlar ----------
def count_commands():
    return one("SELECT COUNT(*) c FROM commands")["c"]


def count_by_cat(cat):
    return one("SELECT COUNT(*) c FROM commands WHERE category=?", (cat,))["c"]


def page_by_cat(cat, offset, limit):
    return many("SELECT * FROM commands WHERE category=? ORDER BY id LIMIT ? OFFSET ?", (cat, limit, offset))


def commands_by_cat(cat):
    return many("SELECT * FROM commands WHERE category=? ORDER BY id", (cat,))


def all_commands():
    return many("SELECT * FROM commands ORDER BY id")


def get_command(cid):
    return one("SELECT * FROM commands WHERE id=?", (cid,))


def get_commands(ids):
    if not ids:
        return []
    rows = many(f"SELECT * FROM commands WHERE id IN ({','.join('?' * len(ids))})", tuple(ids))
    by_id = {r["id"]: r for r in rows}
    return [by_id[i] for i in ids if i in by_id]


def add_command(cat, command, status, descs):
    return run(
        "INSERT INTO commands(category,command,status,desc_uz,desc_en,desc_ru,desc_ar) VALUES(?,?,?,?,?,?,?)",
        (cat, command, status, descs.get("uz"), descs.get("en"), descs.get("ru"), descs.get("ar")))


def update_command(cid, field, value):
    if field not in FIELDS:
        raise ValueError("noto'g'ri maydon")
    run(f"UPDATE commands SET {field}=? WHERE id=?", (value, cid))


def delete_command(cid):
    run("DELETE FROM commands WHERE id=?", (cid,))


# ---------- statistika ----------
def inc(name):
    run("INSERT OR IGNORE INTO stats(name,value) VALUES(?,0)", (name,))
    run("UPDATE stats SET value=value+1 WHERE name=?", (name,))


def get_stat(name):
    r = one("SELECT value FROM stats WHERE name=?", (name,))
    return r["value"] if r else 0
