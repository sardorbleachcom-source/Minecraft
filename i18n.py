# -*- coding: utf-8 -*-
"""Tillar: locales/*.json fayllaridan matn olish."""
import json

import config

_data = {}
RLM = "\u200f"  # o'ngdan-chapga belgisi (arab tili uchun)


def load():
    for lang in config.LANGS:
        with open(config.LOCALES_DIR / f"{lang}.json", encoding="utf-8") as f:
            _data[lang] = json.load(f)


load()


def t(lang, key, **kw):
    s = _data.get(lang, {}).get("ui", {}).get(key)
    if s is None:
        s = _data[config.DEFAULT_LANG]["ui"].get(key, key)
    return s.format(**kw) if kw else s


def cat_name(lang, key):
    return t(lang, "cat_" + key)


def rtl(lang, text):
    """Arab tilida har bir qatorni o'ngdan chapga yo'naltiradi."""
    if lang != "ar":
        return text
    return "\n".join((RLM + ln) if ln.strip() else ln for ln in text.split("\n"))


def desc_of_row(row, lang):
    """Izoh: admin yozgan matn > locales ichidagi tarjima > boshqa til."""
    key = row["desc_key"]
    order = [lang] + [x for x in config.LANGS if x != lang]
    for l in order:
        v = row["desc_" + l]
        if not v and key:
            v = _data[l]["desc"].get(key)
        if v:
            return v
    return "—"
