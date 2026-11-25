""" /start va ro'yxatdan o'tish jarsayoni. """

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .. import database as db
from ..config import ADMIN_ID
from ..keyboards import main_keyboard
from ..utils import safe_edit


async def show_main(update, context: ContextTypes.DEFAULT_TYPE, text: str = None):
    tg_id = update.effective_user.id
    admin = tg_id == ADMIN_ID
    message = text or (
        "🏠 Asosiy menyu\n\nPastdagi tugmalardan birini tanlang:"
    )
    if update.callback_query:
        # Inline xabarni yangilab, reply keyboard ham qo'yamiz
        await update.callback_query.edit_message_text(message)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Tanlang:",
            reply_markup=main_keyboard(admin),
        )
    else:
        await update.message.reply_text(message, reply_markup=main_keyboard(admin))


async def cmd_start(update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    first_name = update.effective_user.first_name or "Foydalanuvchi"

    # Flow larni tozalab turamiz
    context.user_data["flow"] = None
    context.user_data.pop("reg", None)
    context.user_data["quiz"] = None

    if tg_id == ADMIN_ID:
        db.ensure_admin(tg_id, first_name)
        await update.message.reply_text(
            f"👑 Assalomu alaykum, {first_name}! Siz admin sifatida tanildingiz.",
            reply_markup=main_keyboard(True),
        )
        return

    # Ommaviy kirish: /start bosishi bilanoq Telegram ID bo'yicha ro'yxatdan o'tadi.
    # Admin yaratgan login/parol faqat ixtiyoriy qo'shimcha usul bo'lib qoldi.
    user = db.ensure_public_user(tg_id, first_name)
    await update.message.reply_text(
        f"👋 Xush kelibsiz, {user['name']}!\n\n"
        "Siz avtomatik ro'yxatdan o'tdingiz. Endi pastdagi tugmalardan foydalaning.",
        reply_markup=main_keyboard(False),
    )


async def login_command(update, context: ContextTypes.DEFAULT_TYPE):
    """Admin bergan login/parol bilan kirish (ixtiyoriy, eski userlar uchun)."""
    context.user_data["flow"] = "reg_login"
    context.user_data["reg"] = {}
    await update.message.reply_text(
        "Admin bergan loginingizni kiriting:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Bekor qilish", callback_data="flow_cancel")]]
        ),
    )


async def registration_yes(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data["flow"] = "reg_login"
    context.user_data["reg"] = {}
    await safe_edit(
        query,
        "Ro'yxatdan o'tish uchun loginingizni kiriting:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Bekor qilish", callback_data="flow_cancel")]]
        ),
    )


async def registration_no(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data["flow"] = None
    await safe_edit(query, "Ro'yxatdan o'tish bekor qilindi. /start buyrug'ini qayta bosing.")


async def handle_reg_login(update, context: ContextTypes.DEFAULT_TYPE):
    login = update.message.text.strip()
    context.user_data.setdefault("reg", {})["login"] = login
    context.user_data["flow"] = "reg_password"
    await update.message.reply_text("Endi parolingizni kiriting:")


async def handle_reg_password(update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    login = context.user_data.get("reg", {}).get("login", "")
    user = db.get_user_by_login(login)

    if not user or not db.verify_password(password, user["password"]):
        context.user_data["flow"] = "reg_login"
        await update.message.reply_text(
            "❌ Login yoki parol noto'g'ri.\nQaytadan loginni kiriting:"
        )
        return

    if user["registered"] and user["telegram_id"] != update.effective_user.id:
        context.user_data["flow"] = None
        await update.message.reply_text(
            "⛔ Bu login boshqa telegram hisobiga biriktirilgan. Admin bilan bog'laning."
        )
        return

    db.register_user(user["id"], update.effective_user.id)
    context.user_data["flow"] = None
    context.user_data.pop("reg", None)
    await update.message.reply_text(
        f"✅ Tabriklaymiz, {user['name']}! Ro'yxatdan muvaffaqiyatli o'tdingiz.",
        reply_markup=main_keyboard(False),
    )
