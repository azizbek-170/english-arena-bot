"""
Quiz bot kirish nuqtasi.

Ishga tushirish:
    python main.py
"""

import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot import database as db
from bot import keyboards as kb
from bot.config import ADMIN_ID, BOT_TOKEN
from bot.handlers import admin as admin_h
from bot.handlers import quiz as quiz_h
from bot.handlers import start as start_h
from bot.utils import safe_edit

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # har bir so'rovni chiqarmaslik uchun
logger = logging.getLogger("quiz_bot")


async def error_handler(update, context):
    """Tarmoq uzilishlari kabi xatolarni qisqa ko'rinishda loglaydi."""
    logger.warning("Xato: %s", context.error)


def start_health_server():
    """Render Free uchun kichik /health serveri (PORT berilganda ishga tushadi)."""
    port = int(os.getenv("PORT", "0") or 0)
    if not port:
        return None

    class HealthHandler(BaseHTTPRequestHandler):
        def _reply(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")

        def do_GET(self):
            self._reply()

        def do_HEAD(self):
            self._reply()

        def log_message(self, fmt, *args):
            logger.debug("health: " + fmt, *args)

    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, name="health-server", daemon=True).start()
    logger.info("Health server ishga tushdi: port=%s", port)
    return server


# =========================================================================== #
# Matn xabarlarni marshrutizatsiya qilish (barcha kiritish oqimlari shu yerda)
# =========================================================================== #
TEXT_FLOWS = {
    "reg_login": start_h.handle_reg_login,
    "reg_password": start_h.handle_reg_password,
    "arena_title": admin_h.arena_title_text,
    "arena_desc": admin_h.arena_desc_text,
    "q_uz": admin_h.q_uz_text,
    "q_en": admin_h.q_en_text,
    "q_a": admin_h.q_a_text,
    "q_b": admin_h.q_b_text,
    "q_c": admin_h.q_c_text,
    "q_d": admin_h.q_d_text,
    "u_name": admin_h.u_name_text,
    "u_login": admin_h.u_login_text,
    "u_password": admin_h.u_password_text,
    "edit_name": admin_h.edit_name_text,
    "edit_login": admin_h.edit_login_text,
    "edit_pass": admin_h.edit_pass_text,
    "qe_text": admin_h.qe_text,
}


async def text_router(update, context):
    text = (update.message.text or "").strip()
    flow = context.user_data.get("flow")

    # Asosiy menyu tugmalari har qanday holatda ham ishlashi kerak.
    # Agar biror kiritish jarayonida qolib ketgan bo'lsak, uni tozalaymiz.
    if text in (kb.BTN_ADMIN, kb.BTN_ENGLISH, kb.BTN_LOGIN):
        context.user_data["flow"] = None
        context.user_data["quiz"] = None
        for key in ("new_arena", "new_q", "new_user", "reg", "edit_user_id", "edit_q", "import_arena_id"):
            context.user_data.pop(key, None)
        if text == kb.BTN_ADMIN:
            if update.effective_user.id != ADMIN_ID:
                await update.message.reply_text("⛔ Bu bo'lim faqat admin uchun.")
                return
            await update.message.reply_text(
                "👑 ADMIN PANEL\n\nBoshqaruv bo'limini tanlang:",
                reply_markup=kb.admin_menu(),
            )
        elif text == kb.BTN_LOGIN:
            return await start_h.login_command(update, context)
        else:
            await quiz_h.show_english_arenas(update, context)
        return

    # 2-qism: typing javobi
    if context.user_data.get("quiz") and context.user_data["quiz"].get("stage") == "typing":
        await quiz_h.handle_typing(update, context)
        return

    if flow == "q_import_csv":
        if text.lower() in ("/cancel", "bekor", "bekor qilish"):
            context.user_data["flow"] = None
            context.user_data.pop("import_arena_id", None)
            await update.message.reply_text("❌ CSV import bekor qilindi.")
        else:
            await update.message.reply_text("📥 CSV fayl yuboring yoki /cancel yozing.")
        return

    if flow in TEXT_FLOWS:
        await TEXT_FLOWS[flow](update, context)
        return

    # Arenada yotgan boshqa matnlar uchun ogohlantirish
    if context.user_data.get("quiz"):
        await quiz_h.warn_in_arena(update, context)
        return

    await update.message.reply_text(
        "Pastdagi tugmalardan foydalaning yoki /start buyrug'ini bosing."
    )


# =========================================================================== #
# Inline tugmalarni marshrutizatsiya qilish
# =========================================================================== #
async def callback_router(update, context):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    p = data.split(":")
    head = p[0]

    if head == "noop":
        return

    # --- Ro'yxatdan o'tish ---
    if head == "reg_yes":
        return await start_h.registration_yes(update, context)
    if head == "reg_no":
        return await start_h.registration_no(update, context)
    if head == "flow_cancel":
        return await admin_h.flow_cancel(update, context)
    if head == "back_main":
        return await start_h.show_main(update, context)

    # --- Admin menyulari ---
    if head == "adm_menu":
        return await admin_h.admin_menu(update, context)
    if head == "adm_arenas":
        return await admin_h.arena_manage(update, context)
    if head == "adm_users":
        return await admin_h.users_manage(update, context)
    if head == "adm_stats":
        return await admin_h.admin_stats(update, context)
    if head == "adm_export_results":
        return await admin_h.admin_export_results(update, context)
    if head == "arena_manage":
        return await admin_h.arena_manage(update, context)

    # --- Arena qo'shish ---
    if head == "arena_add":
        return await admin_h.arena_add_start(update, context)
    if head == "alvl" and len(p) == 2:
        return await admin_h.arena_level_callback(update, context, p[1])

    # --- Arenalar ---
    if head == "arena_list":
        return await admin_h.arenas_list(update, context)
    if head == "arena" and len(p) == 2:
        return await admin_h.arena_detail(update, context, int(p[1]))
    if head == "atoggle" and len(p) == 2:
        return await admin_h.arena_toggle(update, context, int(p[1]))
    if head == "adel" and len(p) == 2:
        return await admin_h.arena_delete_confirm(update, context, int(p[1]))
    if head == "adel_yes" and len(p) == 2:
        return await admin_h.arena_delete(update, context, int(p[1]))

    # --- Savollar ---
    if head == "qadd" and len(p) == 2:
        return await admin_h.question_add_start(update, context, int(p[1]))
    if head == "qtype" and len(p) == 3:
        return await admin_h.question_type_callback(update, context, p[1], int(p[2]))
    if head == "qcorr" and len(p) == 2:
        return await admin_h.question_correct_callback(update, context, p[1])
    if head == "qlist" and len(p) == 2:
        return await admin_h.questions_list(update, context, int(p[1]))
    if head == "qlist" and len(p) == 3:
        return await admin_h.questions_list(update, context, int(p[1]), page=int(p[2]))
    if head == "qdelmode" and len(p) == 2:
        return await admin_h.questions_list(update, context, int(p[1]), delete_mode=True)
    if head == "qdelmode" and len(p) == 3:
        return await admin_h.questions_list(update, context, int(p[1]), delete_mode=True, page=int(p[2]))
    if head == "qinfo" and len(p) == 3:
        return await admin_h.question_info(update, context, int(p[1]), int(p[2]))
    if head == "qedit" and len(p) == 3:
        return await admin_h.question_edit_menu(update, context, int(p[1]), int(p[2]))
    if head == "qef" and len(p) == 4:
        return await admin_h.question_edit_field_start(update, context, int(p[1]), int(p[2]), p[3])
    if head == "qecorr" and len(p) == 4:
        return await admin_h.question_edit_correct(update, context, int(p[1]), int(p[2]), p[3])
    if head == "qdel" and len(p) == 3:
        return await admin_h.question_delete(update, context, int(p[1]), int(p[2]))
    if head == "qexport" and len(p) == 2:
        return await admin_h.questions_export(update, context, int(p[1]))
    if head == "qimport" and len(p) == 2:
        return await admin_h.question_import_start(update, context, int(p[1]))

    # --- AI lug'at / gap-fill ---
    if head == "aivocab" and len(p) == 2:
        return await admin_h.ai_vocab_start(update, context, int(p[1]))
    if head == "avlvl" and len(p) == 3:
        return await admin_h.ai_vocab_apply(update, context, int(p[1]), p[2], "vocab")
    if head == "aigap" and len(p) == 2:
        return await admin_h.ai_gap_start(update, context, int(p[1]))
    if head == "agvlvl" and len(p) == 3:
        return await admin_h.ai_vocab_apply(update, context, int(p[1]), p[2], "gap")
    if head == "aiidiom" and len(p) == 2:
        return await admin_h.ai_idiom_start(update, context, int(p[1]))
    if head == "aidlvl" and len(p) == 3:
        return await admin_h.ai_vocab_apply(update, context, int(p[1]), p[2], "idiom")

    # --- Userlar ---
    if head == "user_list" and len(p) == 1:
        return await admin_h.users_list(update, context)
    if head == "user_list" and len(p) == 2:
        return await admin_h.users_list(update, context, page=int(p[1]))
    if head == "user_add":
        return await admin_h.user_add_start(update, context)
    if head == "udetail" and len(p) == 2:
        return await admin_h.user_detail(update, context, int(p[1]))
    if head == "uedit_name" and len(p) == 2:
        return await admin_h.user_edit_start(update, context, int(p[1]), "name")
    if head == "uedit_login" and len(p) == 2:
        return await admin_h.user_edit_start(update, context, int(p[1]), "login")
    if head == "uedit_pass" and len(p) == 2:
        return await admin_h.user_edit_start(update, context, int(p[1]), "password")
    if head == "udel" and len(p) == 2:
        return await admin_h.user_delete_confirm(update, context, int(p[1]))
    if head == "udel_yes" and len(p) == 2:
        return await admin_h.user_delete(update, context, int(p[1]))

    # --- Ingliz tili arenasi ---
    if head == "eng_arenas":
        return await quiz_h.show_english_arenas(update, context)
    if head == "my_results":
        return await quiz_h.show_my_results(update, context)
    if head == "leaderboard":
        return await quiz_h.show_leaderboard(update, context)
    if head == "play" and len(p) == 2:
        return await quiz_h.start_quiz(update, context, int(p[1]))
    if head == "qans" and len(p) == 4:
        return await quiz_h.answer_mcq(update, context, int(p[1]), int(p[2]), p[3])
    if head == "cancel_arena_cb":
        return await quiz_h.cancel_arena(update, context)

    await safe_edit(query, "❌ Noma'lum tugma.")


# =========================================================================== #
# Botni ishga tushirish
# =========================================================================== #
async def document_router(update, context):
    if context.user_data.get("flow") == "q_import_csv":
        await admin_h.question_import_document(update, context)
        return
    await update.message.reply_text("Hozir hujjat qabul qilinmaydi. CSV import uchun admin paneldan foydalaning.")


def main():
    start_health_server()
    db.init_db()
    logger.info("Ma'lumotlar bazasi tayyor")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_h.cmd_start))
    application.add_handler(CommandHandler("login", start_h.login_command))
    application.add_handler(CommandHandler("cancel_arena", quiz_h.cancel_arena))
    application.add_handler(CallbackQueryHandler(callback_router))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    application.add_handler(MessageHandler(filters.Document.ALL, document_router))
    application.add_error_handler(error_handler)

    logger.info("Bot ishga tushdi (admin_id=%s)", ADMIN_ID)
    application.run_polling(allowed_updates=["message", "callback_query"])


import asyncio

if __name__ == "__main__":
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  main()
