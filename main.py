# -*- coding: utf-8 -*-
"""Minecraft Buyruqlari — Telegram bot (Minecraft Bedrock Edition)."""
import functools
import html
import logging
import threading
import time

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

import config
import db
import i18n
import keyboards as kbd
from i18n import rtl, t
from search import run_search

log = logging.getLogger("bot")

if not config.BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN topilmadi. .env faylini tekshiring (BOT_TOKEN=...).")

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML", threaded=True)

STATE = {}    # uid -> {"step": str, "data": dict}  (admin jarayonlari, qidiruv)
HISTORY = {}  # uid -> ["menu", "cat:items:0", ...]  ("Orqaga" uchun)
SEARCH = {}   # uid -> (so'rov, [id, ...])
esc = html.escape


def is_admin(uid):
    return uid in config.ADMIN_IDS


def lang_of(uid):
    return db.get_lang(uid) or config.DEFAULT_LANG


def T(lang, key, **kw):
    """Matn + (arab tili bo'lsa) o'ngdan-chapga yo'nalish."""
    return rtl(lang, t(lang, key, **kw))


# ---------- xatolarni ushlash ----------
def _ctx(obj):
    if isinstance(obj, types.CallbackQuery):
        return obj.from_user.id, obj.message.chat.id
    return obj.from_user.id, obj.chat.id


def safe(fn):
    @functools.wraps(fn)
    def wrapper(obj, *a, **k):
        try:
            return fn(obj, *a, **k)
        except ApiTelegramException as e:
            if "message is not modified" in str(e):
                return
            log.error("Telegram API xatosi: %s", e)
        except Exception:
            log.exception("Handlerda xatolik")
            try:
                uid, chat = _ctx(obj)
                bot.send_message(chat, T(lang_of(uid), "err_generic"))
            except Exception:
                log.exception("Xato haqida xabar yuborib bo'lmadi")
    return wrapper


def show(chat_id, msg_id, text, markup=None):
    """msg_id bo'lsa xabarni tahrirlaydi, bo'lmasa yangi yuboradi."""
    if msg_id:
        try:
            bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, disable_web_page_preview=True)
            return
        except ApiTelegramException as e:
            if "message is not modified" in str(e):
                return
            log.warning("Tahrirlab bo'lmadi, yangi xabar yuboriladi: %s", e)
    bot.send_message(chat_id, text, reply_markup=markup, disable_web_page_preview=True)


# ---------- ekranlar ----------
def card(lang, r, n=None, admin=False):
    head = f"<b>{n}. {t(lang, 'lbl_cmd')}</b>" if n else f"<b>{t(lang, 'lbl_cmd')}</b>"
    st = r["status"] if r["status"] in ("ok", "ver", "no") else "ok"
    tail = (f"{t(lang, 'lbl_desc')} {esc(i18n.desc_of_row(r, lang))}\n"
            f"{t(lang, 'lbl_bedrock')} {t(lang, 'st_' + st)}\n"
            f"{t(lang, 'lbl_copy')} {t(lang, 'copy_hint')}")
    if admin:
        tail += f"\n🆔 ID: {r['id']}"
    return rtl(lang, head) + f"\n<pre>{esc(r['command'])}</pre>\n" + rtl(lang, tail)


def list_screen(uid, lang, title, total, page, fetch, prefix):
    ps = config.PAGE_SIZE
    pages = max(1, -(-total // ps))
    page = min(max(page, 0), pages - 1)
    if total == 0:
        return T(lang, "empty"), kbd.nav(lang)
    rows = fetch(page * ps, ps)
    parts = [rtl(lang, f"<b>{title}</b>\n{t(lang, 'page_info', page=page + 1, pages=pages, total=total)}")]
    admin = is_admin(uid)
    for i, r in enumerate(rows, start=page * ps + 1):
        parts.append(card(lang, r, i, admin))
    prev_t = f"{prefix}:{page - 1}" if page > 0 else None
    next_t = f"{prefix}:{page + 1}" if page < pages - 1 else None
    return "\n\n".join(parts), kbd.nav(lang, prev_t, next_t)


def build(uid, lang, target):
    kind, _, rest = target.partition(":")
    if kind == "cat":
        key, _, p = rest.partition(":")
        if key in config.CATEGORIES:
            return list_screen(uid, lang, t(lang, "cat_" + key), db.count_by_cat(key),
                               int(p or 0), lambda o, l: db.page_by_cat(key, o, l), f"cat:{key}")
    elif kind == "res":
        s = SEARCH.get(uid)
        if not s:
            return T(lang, "search_expired"), kbd.nav(lang)
        q, ids = s
        title = t(lang, "search_found", q=esc(q), n=len(ids))
        return list_screen(uid, lang, title, len(ids), int(rest or 0),
                           lambda o, l: db.get_commands(ids[o:o + l]), "res")
    elif kind == "search":
        return T(lang, "search_prompt"), kbd.nav(lang)
    elif kind == "about":
        return T(lang, "about", count=db.count_commands()), kbd.nav(lang)
    elif kind == "help":
        return T(lang, "help"), kbd.nav(lang)
    return T(lang, "menu"), kbd.menu(lang, is_admin(uid))


def go(uid, chat_id, msg_id, target, record=True):
    lang = lang_of(uid)
    kind = target.partition(":")[0]
    if kind == "search":
        STATE[uid] = {"step": "search", "data": {}}
    if kind in ("cat", "res"):
        db.inc("views")
    text, markup = build(uid, lang, target)
    if record:
        if target == "menu":
            HISTORY[uid] = ["menu"]
        else:
            h = HISTORY.setdefault(uid, ["menu"])
            if h[-1] != target:
                h.append(target)
            del h[:-20]
    show(chat_id, msg_id, text, markup)


def send_welcome(uid, chat_id, msg_id, user):
    lang = lang_of(uid)
    HISTORY[uid] = ["menu"]
    STATE.pop(uid, None)
    text = T(lang, "welcome", name=esc(user.first_name or ""))
    show(chat_id, msg_id, text, kbd.menu(lang, is_admin(uid)))


def do_user_search(uid, chat_id, text):
    lang = lang_of(uid)
    db.inc("searches")
    ids = run_search(text)
    if not ids:
        bot.send_message(chat_id, T(lang, "search_none", q=esc(text[:60])), reply_markup=kbd.nav(lang))
        return
    SEARCH[uid] = (text[:60], ids)
    go(uid, chat_id, None, "res:0")


# ---------- buyruqlar (/start, /menu ...) ----------
@bot.message_handler(commands=["start"])
@safe
def cmd_start(m):
    uid = m.from_user.id
    db.upsert_user(m.from_user)
    STATE.pop(uid, None)
    if not db.get_lang(uid):
        bot.send_message(m.chat.id, t("uz", "choose_lang"), reply_markup=kbd.lang_picker())
        return
    send_welcome(uid, m.chat.id, None, m.from_user)


@bot.message_handler(commands=["menu"])
@safe
def cmd_menu(m):
    db.upsert_user(m.from_user)
    if not db.get_lang(m.from_user.id):
        return cmd_start(m)
    STATE.pop(m.from_user.id, None)
    go(m.from_user.id, m.chat.id, None, "menu")


@bot.message_handler(commands=["help"])
@safe
def cmd_help(m):
    db.upsert_user(m.from_user)
    if not db.get_lang(m.from_user.id):
        return cmd_start(m)
    go(m.from_user.id, m.chat.id, None, "help")


@bot.message_handler(commands=["language", "lang"])
@safe
def cmd_language(m):
    db.upsert_user(m.from_user)
    bot.send_message(m.chat.id, t("uz", "choose_lang"), reply_markup=kbd.lang_picker())


@bot.message_handler(commands=["admin"])
@safe
def cmd_admin(m):
    uid = m.from_user.id
    if not is_admin(uid):
        return bot.send_message(m.chat.id, T(lang_of(uid), "adm_no_access"))
    STATE.pop(uid, None)
    admin_panel(uid, m.chat.id, None)


@bot.message_handler(commands=["broadcast"])
@safe
def cmd_broadcast(m):
    uid = m.from_user.id
    if not is_admin(uid):
        return bot.send_message(m.chat.id, T(lang_of(uid), "adm_no_access"))
    text = m.text.partition(" ")[2].strip()
    if not text:
        return bot.send_message(m.chat.id, t(lang_of(uid), "adm_bc_usage"))
    do_broadcast(m.chat.id, uid, text)


# ---------- admin ----------
def admin_panel(uid, chat_id, msg_id):
    lang = lang_of(uid)
    show(chat_id, msg_id, t(lang, "adm_panel", users=db.count_users(), cmds=db.count_commands()),
         kbd.admin_panel(lang))


def do_broadcast(chat_id, uid, text):
    lang = lang_of(uid)
    ids = db.all_user_ids()
    bot.send_message(chat_id, t(lang, "adm_bc_start", n=len(ids)))

    def job():
        ok = fail = 0
        for i in ids:
            try:
                bot.send_message(i, "📢 " + text, parse_mode=None)
                ok += 1
            except Exception:
                fail += 1
            time.sleep(0.05)
        try:
            bot.send_message(chat_id, t(lang, "adm_bc_done", ok=ok, fail=fail))
        except Exception:
            log.exception("Broadcast hisobotini yuborib bo'lmadi")

    threading.Thread(target=job, daemon=True).start()


def show_stats(uid, chat_id, msg_id):
    lang = lang_of(uid)
    now = int(time.time())
    lc = db.lang_counts()
    text = t(lang, "adm_stats", users=db.count_users(), new=db.joined_since(now - 86400),
             active=db.active_since(now - 86400), uz=lc.get("uz", 0), en=lc.get("en", 0),
             ru=lc.get("ru", 0), ar=lc.get("ar", 0), cmds=db.count_commands(),
             views=db.get_stat("views"), searches=db.get_stat("searches"))
    show(chat_id, msg_id, text, kbd.admin_panel(lang))


def _norm_cmd(text):
    text = text.strip()
    return text if text.startswith("/") else "/" + text


def _ask_desc(chat, lang, code):
    bot.send_message(chat, t(lang, "adm_ask_desc", code=code.upper()))


def admin_text(m, st):
    uid, chat = m.from_user.id, m.chat.id
    lang = lang_of(uid)
    text = m.text.strip()
    step, d = st["step"], st["data"]

    if step == "bc":
        d["text"] = text
        st["step"] = "bc_confirm"
        bot.send_message(chat, t(lang, "adm_bc_confirm", n=db.count_users(), text=esc(text)),
                         reply_markup=kbd.confirm(lang, "adm:bcok"))
    elif step == "add_cmd":
        d["command"] = _norm_cmd(text)
        st["step"] = "add_st"
        bot.send_message(chat, t(lang, "adm_pick_status"), reply_markup=kbd.status_picker(lang, "adm:st:"))
    elif step.startswith("add_d_"):
        code = step[-2:]
        d["desc_" + code] = None if text == "-" else text
        idx = config.LANGS.index(code)
        if idx + 1 < len(config.LANGS):
            nxt = config.LANGS[idx + 1]
            st["step"] = "add_d_" + nxt
            _ask_desc(chat, lang, nxt)
        else:
            cid = db.add_command(d["cat"], d["command"], d["st"], {l: d.get("desc_" + l) for l in config.LANGS})
            STATE.pop(uid, None)
            bot.send_message(chat, t(lang, "adm_added", id=cid), reply_markup=kbd.admin_panel(lang))
    elif step == "edit_id" or step == "del_id":
        if not text.isdigit():
            return bot.send_message(chat, t(lang, "adm_bad_id"))
        r = db.get_command(int(text))
        if not r:
            return bot.send_message(chat, t(lang, "adm_not_found"))
        if step == "edit_id":
            STATE[uid] = {"step": "edit_pick", "data": {"id": r["id"]}}
            bot.send_message(chat, card(lang, r, None, True) + "\n\n" + t(lang, "adm_pick_field"),
                             reply_markup=kbd.edit_fields(lang))
        else:
            STATE.pop(uid, None)
            bot.send_message(chat, card(lang, r, None, True) + "\n\n" + t(lang, "adm_confirm_del"),
                             reply_markup=kbd.confirm(lang, f"adm:dok:{r['id']}"))
    elif step == "edit_val":
        field = d["field"]
        value = _norm_cmd(text) if field == "command" else (None if (text == "-" and field.startswith("desc_")) else text)
        db.update_command(d["id"], field, value)
        STATE.pop(uid, None)
        bot.send_message(chat, t(lang, "adm_updated") + "\n\n" + card(lang, db.get_command(d["id"]), None, True),
                         reply_markup=kbd.admin_panel(lang))
    else:
        STATE.pop(uid, None)


def admin_cb(c):
    uid, chat, mid = c.from_user.id, c.message.chat.id, c.message.message_id
    lang = lang_of(uid)
    d = c.data
    if not is_admin(uid):
        return t(lang, "adm_no_access")
    st = STATE.get(uid)

    if d == "adm":
        STATE.pop(uid, None)
        admin_panel(uid, chat, mid)
    elif d == "adm:cancel":
        STATE.pop(uid, None)
        show(chat, mid, t(lang, "adm_cancelled"), kbd.admin_panel(lang))
    elif d == "adm:stats":
        show_stats(uid, chat, mid)
    elif d == "adm:bc":
        STATE[uid] = {"step": "bc", "data": {}}
        show(chat, mid, t(lang, "adm_bc_prompt"), kbd.cancel(lang))
    elif d == "adm:bcok":
        if st and st["step"] == "bc_confirm":
            text = st["data"]["text"]
            STATE.pop(uid, None)
            do_broadcast(chat, uid, text)
    elif d == "adm:add":
        STATE[uid] = {"step": "add_cat", "data": {}}
        show(chat, mid, t(lang, "adm_pick_cat"), kbd.cat_picker(lang, "adm:cat:"))
    elif d.startswith("adm:cat:") and st and st["step"] == "add_cat":
        st["data"]["cat"] = d.split(":")[2]
        st["step"] = "add_cmd"
        show(chat, mid, t(lang, "adm_ask_cmd"), kbd.cancel(lang))
    elif d.startswith("adm:st:") and st and st["step"] == "add_st":
        st["data"]["st"] = d.split(":")[2]
        st["step"] = "add_d_uz"
        show(chat, mid, t(lang, "adm_ask_desc", code="UZ"))
    elif d == "adm:edit":
        STATE[uid] = {"step": "edit_id", "data": {}}
        show(chat, mid, t(lang, "adm_ask_id"), kbd.cancel(lang))
    elif d.startswith("adm:ef:") and st and st["step"] == "edit_pick":
        field = d.split(":")[2]
        if field == "category":
            show(chat, mid, t(lang, "adm_pick_cat"), kbd.cat_picker(lang, "adm:ec:"))
        elif field == "status":
            show(chat, mid, t(lang, "adm_pick_status"), kbd.status_picker(lang, "adm:es:"))
        else:
            st["step"] = "edit_val"
            st["data"]["field"] = field
            show(chat, mid, t(lang, "adm_ask_value", field=field))
    elif (d.startswith("adm:ec:") or d.startswith("adm:es:")) and st and st["step"] == "edit_pick":
        field = "category" if d.startswith("adm:ec:") else "status"
        db.update_command(st["data"]["id"], field, d.split(":")[2])
        r = db.get_command(st["data"]["id"])
        STATE.pop(uid, None)
        show(chat, mid, t(lang, "adm_updated") + "\n\n" + card(lang, r, None, True), kbd.admin_panel(lang))
    elif d == "adm:del":
        STATE[uid] = {"step": "del_id", "data": {}}
        show(chat, mid, t(lang, "adm_ask_id"), kbd.cancel(lang))
    elif d.startswith("adm:dok:"):
        db.delete_command(int(d.split(":")[2]))
        show(chat, mid, t(lang, "adm_deleted"), kbd.admin_panel(lang))
    return None


# ---------- tugmalar (callback) ----------
@bot.callback_query_handler(func=lambda c: True)
@safe
def on_callback(c):
    toast = None
    try:
        uid, chat, mid = c.from_user.id, c.message.chat.id, c.message.message_id
        d = c.data or ""
        db.upsert_user(c.from_user)
        if d.startswith("lang:"):
            code = d.split(":")[1]
            if code in config.LANGS:
                db.set_lang(uid, code)
                send_welcome(uid, chat, mid, c.from_user)
                toast = t(code, "lang_saved")
        elif d == "chlang":
            show(chat, mid, t("uz", "choose_lang"), kbd.lang_picker())
        elif d.startswith("g:"):
            if not db.get_lang(uid):
                show(chat, mid, t("uz", "choose_lang"), kbd.lang_picker())
            else:
                go(uid, chat, mid, d[2:])
        elif d == "b":
            h = HISTORY.get(uid, ["menu"])
            if len(h) > 1:
                h.pop()
            go(uid, chat, mid, h[-1], record=False)
        elif d.startswith("adm"):
            toast = admin_cb(c)
        else:
            toast = t(lang_of(uid), "err_expired")
    finally:
        try:
            bot.answer_callback_query(c.id, toast)
        except Exception:
            pass


# ---------- oddiy matn = qidiruv (yoki admin jarayoni) ----------
@bot.message_handler(content_types=["text"])
@safe
def on_text(m):
    uid = m.from_user.id
    db.upsert_user(m.from_user)
    if not db.get_lang(uid):
        return bot.send_message(m.chat.id, t("uz", "choose_lang"), reply_markup=kbd.lang_picker())
    st = STATE.get(uid)
    if st and is_admin(uid) and st["step"] != "search":
        return admin_text(m, st)
    STATE.pop(uid, None)
    do_user_search(uid, m.chat.id, m.text.strip())


def main():
    db.init()
    try:
        bot.remove_webhook()
    except Exception:
        pass
    log.info("✅ Bot ishga tushdi. Buyruqlar soni: %s", db.count_commands())
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except KeyboardInterrupt:
            log.info("To'xtatildi.")
            break
        except Exception:
            log.exception("Polling to'xtadi. 5 soniyadan so'ng qayta ishga tushadi...")
            time.sleep(5)


if __name__ == "__main__":
    main()
