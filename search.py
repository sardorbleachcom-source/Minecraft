# -*- coding: utf-8 -*-
"""Qidiruv: kategoriya nomi (4 tilda) yoki buyruq/izoh matni bo'yicha."""
import re

import config
import db
import i18n


def norm(s):
    s = (s or "").lower()
    s = re.sub(r"[‘’ʻ`´]", "'", s)
    s = re.sub(r"[^\w\s'@~/^\[\]=!\-]", " ", s)  # emojilarni olib tashlaydi
    return re.sub(r"\s+", " ", s).strip()


def run_search(text, limit=60):
    qn = norm(text).lstrip("/").strip()
    if len(qn) < 2:
        return []
    hits, seen = [], set()

    def add(i):
        if i not in seen:
            seen.add(i)
            hits.append(i)

    for key in config.CATEGORIES:
        labels = {norm(key)} | {norm(i18n.cat_name(l, key)) for l in config.LANGS}
        if any(qn == x or (len(qn) >= 3 and (qn in x or x in qn)) for x in labels):
            for r in db.commands_by_cat(key):
                add(r["id"])

    for r in db.all_commands():
        blob = norm(r["command"]) + " " + " ".join(norm(i18n.desc_of_row(r, l)) for l in config.LANGS)
        if qn in blob:
            add(r["id"])
    return hits[:limit]
