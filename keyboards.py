# -*- coding: utf-8 -*-
"""Inline tugmalar."""
from telebot import types

import config
from i18n import t


def _b(text, cb):
    return types.InlineKeyboardButton(text, callback_data=cb)


def lang_picker():
    m = types.InlineKeyboardMarkup()
    m.row(_b(t("uz", "lang_uz"), "lang:uz"), _b(t("uz", "lang_en"), "lang:en"))
    m.row(_b(t("uz", "lang_ru"), "lang:ru"), _b(t("uz", "lang_ar"), "lang:ar"))
    return m


def menu(lang, admin=False):
    m = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for key in config.MENU_ORDER:
        if key == "search":
            cb = "g:search"
        elif key == "about":
            cb = "g:about"
        else:
            cb = f"g:cat:{key}:0"
        btns.append(_b(t(lang, "cat_" + key), cb))
    m.add(*btns)
    m.row(_b(t(lang, "change_lang"), "chlang"), _b(t(lang, "help_btn"), "g:help"))
    if admin:
        m.row(_b("🛠 Admin", "adm"))
    return m


def nav(lang, prev_t=None, next_t=None):
    m = types.InlineKeyboardMarkup()
    row = []
    if prev_t:
        row.append(_b(t(lang, "prev"), "g:" + prev_t))
    if next_t:
        row.append(_b(t(lang, "next"), "g:" + next_t))
    if row:
        m.row(*row)
    m.row(_b(t(lang, "back"), "b"), _b(t(lang, "home"), "g:menu"))
    return m


# ---------- admin ----------
def admin_panel(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(_b(t(lang, "adm_b_stats"), "adm:stats"), _b(t(lang, "adm_b_bc"), "adm:bc"),
          _b(t(lang, "adm_b_add"), "adm:add"), _b(t(lang, "adm_b_edit"), "adm:edit"),
          _b(t(lang, "adm_b_del"), "adm:del"))
    m.row(_b(t(lang, "home"), "g:menu"))
    return m


def cat_picker(lang, prefix):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(*[_b(t(lang, "cat_" + k), prefix + k) for k in config.CATEGORIES])
    m.row(_b(t(lang, "adm_b_cancel"), "adm:cancel"))
    return m


def status_picker(lang, prefix):
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(*[_b(t(lang, "st_" + s), prefix + s) for s in ("ok", "ver", "no")])
    m.row(_b(t(lang, "adm_b_cancel"), "adm:cancel"))
    return m


def edit_fields(lang):
    m = types.InlineKeyboardMarkup(row_width=2)
    fields = ["command", "category", "status", "desc_uz", "desc_en", "desc_ru", "desc_ar"]
    m.add(*[_b(t(lang, "adm_f_" + f), "adm:ef:" + f) for f in fields])
    m.row(_b(t(lang, "adm_b_cancel"), "adm:cancel"))
    return m


def confirm(lang, yes_cb, no_cb="adm:cancel"):
    m = types.InlineKeyboardMarkup()
    m.row(_b(t(lang, "adm_b_yes"), yes_cb), _b(t(lang, "adm_b_cancel"), no_cb))
    return m


def cancel(lang):
    m = types.InlineKeyboardMarkup()
    m.row(_b(t(lang, "adm_b_cancel"), "adm:cancel"))
    return m
