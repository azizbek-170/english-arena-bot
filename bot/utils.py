"""Kichik yordamchi funksiyalar."""

from telegram.error import BadRequest


async def safe_edit(query, text: str, reply_markup=None):
    """Xabar o'zgarmaganda Telegram yuboradigan xatolikni jim yutadi."""
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    except BadRequest:
        pass


def is_admin(tg_id: int) -> bool:
    from .config import ADMIN_ID

    return tg_id == ADMIN_ID


def normalize_answer(text: str) -> str:
    """Typing javobini solishtirish uchun tozalaydi."""
    cleaned = (text or "").strip().lower().replace("’", "'").replace("‘", "'")
    cleaned = " ".join(cleaned.split())
    return cleaned.rstrip(".!?,;:")
