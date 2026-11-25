"""Admin panel: English arena boshqaruvi va Userlar boshqaruvi."""

from telegram import InlineKeyboardMarkup

from .. import database as db
from .. import keyboards as kb
from ..config import ADMIN_ID
from ..utils import safe_edit
from ..vocabulary import get_idiom_info


def _admin(update) -> bool:
    return update.effective_user.id == ADMIN_ID


async def _edit(update, text: str, markup: InlineKeyboardMarkup = None):
    await safe_edit(update.callback_query, text, markup)


# =========================================================================== #
# Asosiy admin menyusi
# =========================================================================== #
async def admin_menu(update, context):
    if not _admin(update):
        await _edit(update, "⛔ Bu bo'lim faqat admin uchun.")
        return
    context.user_data["flow"] = None
    await _edit(
        update,
        "👑 ADMIN PANEL\n\nBoshqaruv bo'limini tanlang:",
        kb.admin_menu(),
    )


async def arena_manage(update, context):
    if not _admin(update):
        return
    context.user_data["flow"] = None
    await _edit(update, "🏟 ENGLISH ARENA BOSHQARUVI", kb.arena_manage_menu())


async def users_manage(update, context):
    if not _admin(update):
        return
    context.user_data["flow"] = None
    await _edit(update, "👥 USERLAR BOSHQARUVI", kb.users_manage_menu())


def _fmt_percent(value):
    if value is None:
        return "0"
    return f"{float(value):g}"


async def admin_stats(update, context):
    if not _admin(update):
        return
    stats = db.get_admin_stats()
    lines = [
        "📊 BOT STATISTIKASI\n",
        f"👥 Userlar: {stats.get('users_count', 0)} (ro'yxatdan o'tgan: {stats.get('registered_count', 0)})",
        f"🏟 Arenalar: {stats.get('arenas_count', 0)} (ochiq: {stats.get('open_arenas_count', 0)})",
        f"❓ Savollar: {stats.get('questions_count', 0)}",
        f"📝 Natijalar: {stats.get('results_count', 0)}",
        f"📈 O'rtacha foiz: {_fmt_percent(stats.get('avg_percent'))}%",
    ]
    top_arenas = stats.get("top_arenas") or []
    if top_arenas:
        lines.append("\nTop arenalar:")
        for a in top_arenas:
            lines.append(
                f"• {a['title']} ({a['level']}) — {a['attempts']} urinish, o'rtacha {_fmt_percent(a['avg_percent'])}%"
            )
    await _edit(update, "\n".join(lines), kb.admin_menu())


# =========================================================================== #
# Arena qo'shish
# =========================================================================== #
async def arena_add_start(update, context):
    context.user_data["flow"] = "arena_title"
    context.user_data["new_arena"] = {}
    await _edit(update, "Arena nomini kiriting (masalan: A1 Vocabulary Cup):")


async def arena_title_text(update, context):
    context.user_data["new_arena"]["title"] = update.message.text.strip()
    context.user_data["flow"] = "arena_desc"
    await update.message.reply_text("Arena tavsifini kiriting:")


async def arena_desc_text(update, context):
    context.user_data["new_arena"]["description"] = update.message.text.strip()
    context.user_data["flow"] = "arena_level"
    await update.message.reply_text(
        "Arena darajasini tanlang:", reply_markup=kb.levels_keyboard("alvl")
    )


async def arena_level_callback(update, context, level: str):
    data = context.user_data.get("new_arena", {})
    arena = db.create_arena(data.get("title", "Arena"), data.get("description", ""), level)
    context.user_data["flow"] = None
    context.user_data.pop("new_arena", None)
    await _edit(
        update,
        f"✅ Arena yaratildi:\n\n🏟 {arena['title']}\n📝 {arena['description']}\n🎚 Daraja: {arena['level']}",
        kb.arena_detail_keyboard(arena),
    )


# =========================================================================== #
# Arenalar ro'yxati va detail
# =========================================================================== #
async def arenas_list(update, context):
    arenas = db.list_arenas()
    text = "📋 ARENALAR RO'YXATI\n\n" if arenas else "📋 Hali arena yo'q."
    await _edit(update, text + "Arenani tanlang:", kb.arenas_list_keyboard(arenas))


async def arena_detail(update, context, arena_id: int):
    arena = db.get_arena(arena_id)
    if not arena:
        await _edit(update, "❌ Arena topilmadi.", kb.back_button("arena_list"))
        return
    count = len(db.list_questions(arena_id))
    status = "🟢 OCHIQ" if arena["is_open"] else "🔴 YOPIQ"
    text = (
        f"🏟 {arena['title']}\n"
        f"📝 {arena['description']}\n"
        f"🎚 Daraja: {arena['level']} ({db_level_points(arena['level'])} achko/savol)\n"
        f"📊 Holat: {status}\n"
        f"❓ Savollar soni: {count}"
    )
    await _edit(update, text, kb.arena_detail_keyboard(arena))


def db_level_points(level: str) -> int:
    from ..config import LEVEL_POINTS

    return LEVEL_POINTS.get(level, 1)


async def arena_toggle(update, context, arena_id: int):
    db.toggle_arena(arena_id)
    await arena_detail(update, context, arena_id)


async def arena_delete_confirm(update, context, arena_id: int):
    from ..keyboards import confirm_keyboard

    await _edit(
        update,
        "❗ Arenani o'chirishni tasdiqlaysizmi? Unga tegishli barcha savollar ham o'chadi.",
        confirm_keyboard(f"adel_yes:{arena_id}", "arena_list"),
    )


async def arena_delete(update, context, arena_id: int):
    db.delete_arena(arena_id)
    await arenas_list(update, context)


# =========================================================================== #
# Savol qo'shish
# =========================================================================== #
async def question_add_start(update, context, arena_id: int):
    context.user_data["flow"] = None
    context.user_data["new_q"] = {"arena_id": arena_id}
    await _edit(update, "Savol turini tanlang:", kb.question_type_keyboard(arena_id))


async def question_type_callback(update, context, qtype: str, arena_id: int):
    context.user_data["new_q"] = {"arena_id": arena_id, "qtype": qtype}
    context.user_data["flow"] = "q_uz"
    prompts = {
        "vocab": "✏️ O'zbekcha so'zni kiriting:",
        "gap": "✏️ Nuqtali gapni yozing (masalan: I ___ to school.):",
        "idiom": "✏️ Idiomni kiriting (masalan: At all costs):",
    }
    await _edit(update, prompts.get(qtype, prompts["vocab"]))


async def q_uz_text(update, context):
    context.user_data["new_q"]["uz"] = update.message.text.strip()
    context.user_data["flow"] = "q_en"
    qtype = context.user_data["new_q"].get("qtype", "vocab")
    prompts = {
        "vocab": "Inglizcha to'g'ri javobni kiriting:",
        "gap": "Nuqta o'rniga keladigan so'zni kiriting:",
        "idiom": "Idiom o'zini kiriting (typing bosqichi uchun):",
    }
    await update.message.reply_text(prompts.get(qtype, prompts["vocab"]))


def _option_prompt(qtype: str, letter: str) -> str:
    suffix = " (ma'no/definition)" if qtype == "idiom" else ""
    return f"{letter} variantni kiriting{suffix}:"


async def q_en_text(update, context):
    context.user_data["new_q"]["en"] = update.message.text.strip()
    context.user_data["flow"] = "q_a"
    qtype = context.user_data["new_q"].get("qtype", "vocab")
    await update.message.reply_text(_option_prompt(qtype, "A"))


async def q_a_text(update, context):
    context.user_data["new_q"]["a"] = update.message.text.strip()
    context.user_data["flow"] = "q_b"
    qtype = context.user_data["new_q"].get("qtype", "vocab")
    await update.message.reply_text(_option_prompt(qtype, "B"))


async def q_b_text(update, context):
    context.user_data["new_q"]["b"] = update.message.text.strip()
    context.user_data["flow"] = "q_c"
    qtype = context.user_data["new_q"].get("qtype", "vocab")
    await update.message.reply_text(_option_prompt(qtype, "C"))


async def q_c_text(update, context):
    context.user_data["new_q"]["c"] = update.message.text.strip()
    context.user_data["flow"] = "q_d"
    qtype = context.user_data["new_q"].get("qtype", "vocab")
    await update.message.reply_text(_option_prompt(qtype, "D"))


async def q_d_text(update, context):
    context.user_data["new_q"]["d"] = update.message.text.strip()
    context.user_data["flow"] = "q_correct"
    await update.message.reply_text(
        "To'g'ri javob harfini tanlang:", reply_markup=kb.letters_keyboard("qcorr")
    )


async def question_correct_callback(update, context, letter: str):
    data = context.user_data.get("new_q", {})
    arena_id = data.get("arena_id")
    if not arena_id:
        await _edit(update, "❌ Savol qo'shish jarayoni tugagan.", kb.back_button("arena_list"))
        return
    db.add_question(
        arena_id,
        data.get("uz", ""),
        data.get("en", ""),
        data.get("a", ""),
        data.get("b", ""),
        data.get("c", ""),
        data.get("d", ""),
        letter,
        data.get("qtype", "vocab"),
    )
    context.user_data["flow"] = None
    context.user_data.pop("new_q", None)
    await arena_detail(update, context, arena_id)


async def questions_list(update, context, arena_id: int, delete_mode=False):
    questions = db.list_questions(arena_id)
    if not questions:
        await _edit(
            update,
            "❌ Bu arenada savol yo'q.",
            kb.back_button(f"arena:{arena_id}"),
        )
        return
    title = "🗑 SAVOL O'CHIRISH" if delete_mode else "📋 SAVOLLAR RO'YXATI"
    text = (
        f"{title}\n"
        f"Arena: {db.get_arena(arena_id)['title']}\n"
        f"Jami: {len(questions)} ta\n\n"
        "Savolni tanlang:"
    )
    await _edit(update, text, kb.questions_keyboard(questions, arena_id, delete_mode))


async def question_info(update, context, question_id: int, arena_id: int):
    q = db.get_question(question_id)
    if not q:
        await _edit(update, "❌ Savol topilmadi.", kb.back_button(f"arena:{arena_id}"))
        return
    qtype = q.get("question_type", "vocab")
    labels = {
        "gap": ("Gap to'ldirish (gap filling)", "Gap"),
        "idiom": ("Idiom (definition + tarjima)", "Idiom"),
    }
    qtype_label, word_label = labels.get(qtype, ("Lug'at so'zi", "O'zbekcha"))
    text = (
        f"❓ Savol #{q['id']}\n"
        f"🏷 Turi: {qtype_label}\n\n"
        f"{word_label}: {q['uz_word']}\n"
        f"To'g'ri javob: {q['en_word']}\n\n"
        f"a) {q['opt_a']}\n"
        f"b) {q['opt_b']}\n"
        f"c) {q['opt_c']}\n"
        f"d) {q['opt_d']}\n\n"
        f"✅ To'g'ri variant: {q['correct'].upper()}"
    )
    if qtype == "idiom":
        info = get_idiom_info(q["en_word"]) or {}
        text += (
            f"\n\n📖 Definition: {info.get('definition', '-')}"
            f"\n🇺🇿 Tarjima: {info.get('uzbek', '-')}"
        )
    await _edit(update, text, kb.back_button(f"qlist:{arena_id}"))


async def question_delete(update, context, question_id: int, arena_id: int):
    db.delete_question(question_id)
    await questions_list(update, context, arena_id, delete_mode=True)


# =========================================================================== #
# AI orqali lug'at qo'shish
# =========================================================================== #
AI_LABELS = {
    "vocab": ("avlvl", "🤖 AI lug'at qo'shish", "lug'at"),
    "gap": ("agvlvl", "🤖 AI gap-fill qo'shish", "gap-fill"),
    "idiom": ("aidlvl", "🤖 AI idiom qo'shish", "idiom"),
}


async def ai_vocab_start(update, context, arena_id: int, qtype: str = "vocab"):
    from ..keyboards import levels_keyboard

    # Eski "qo'lda savol qo'shish" oqimi qolib ketmasligi uchun
    context.user_data["flow"] = None
    context.user_data.pop("new_q", None)

    prefix, title, _ = AI_LABELS.get(qtype, AI_LABELS["vocab"])
    await _edit(
        update,
        f"{title}\n\nDarajani tanlang (savollar shu darajaga mos yuboriladi):",
        levels_keyboard(f"{prefix}:{arena_id}"),
    )


async def ai_gap_start(update, context, arena_id: int):
    await ai_vocab_start(update, context, arena_id, qtype="gap")


async def ai_idiom_start(update, context, arena_id: int):
    await ai_vocab_start(update, context, arena_id, qtype="idiom")


async def ai_vocab_apply(update, context, arena_id: int, level: str, qtype: str = "vocab"):
    from ..vocabulary import get_vocabulary

    items = get_vocabulary(level, qtype)
    added = db.add_questions_bulk(arena_id, items, qtype)
    context.user_data["flow"] = None
    context.user_data.pop("new_q", None)
    arena = db.get_arena(arena_id)
    _, _, label = AI_LABELS.get(qtype, AI_LABELS["vocab"])
    extra = "\n💬 To'g'ri idiom javobi har bosqichda 3 achko beradi." if qtype == "idiom" else ""
    await _edit(
        update,
        f"✅ {level} darajasi uchun {added} ta {label} savoli qo'shildi.{extra}\n\n"
        f"🏟 {arena['title']}\n❓ Jami savollar: {len(db.list_questions(arena_id))}",
        kb.arena_detail_keyboard(arena),
    )


# =========================================================================== #
# Userlar boshqaruvi
# =========================================================================== #
async def users_list(update, context):
    users = db.list_users()
    text = "👥 USERLAR RO'YXATI\n\n" if users else "👥 Hali user yo'q."
    await _edit(update, text + "User yoki amalni tanlang:", kb.users_list_keyboard(users))


async def user_add_start(update, context):
    context.user_data["flow"] = "u_name"
    context.user_data["new_user"] = {}
    await _edit(update, "Yangi user ismini (username) kiriting:")


async def u_name_text(update, context):
    context.user_data["new_user"]["name"] = update.message.text.strip()
    context.user_data["flow"] = "u_login"
    await update.message.reply_text("Login kiriting:")


async def u_login_text(update, context):
    login = update.message.text.strip()
    if db.get_user_by_login(login):
        await update.message.reply_text("❌ Bunday login bor. Boshqa login kiriting:")
        return
    context.user_data["new_user"]["login"] = login
    context.user_data["flow"] = "u_password"
    await update.message.reply_text("Parol kiriting:")


async def u_password_text(update, context):
    data = context.user_data.get("new_user", {})
    password = update.message.text.strip()
    user = db.create_user(data.get("name", ""), data.get("login", ""), password)
    context.user_data["flow"] = None
    context.user_data.pop("new_user", None)
    await update.message.reply_text(
        f"✅ User yaratildi:\n\n👤 {user['name']}\n🔑 Login: {user['login']}\n"
        f"🔒 Parol: {password}\n\n"
        "Endi bu login va parol bilan botda ro'yxatdan o'tish mumkin."
    )
    await users_list_from_message(update, context)


async def users_list_from_message(update, context):
    # Yangi user yaratilgandan keyin ro'yxatni yangi xabar bilan ko'rsatish
    users = db.list_users()
    await update.message.reply_text(
        "👥 USERLAR RO'YXATI\n\nUser yoki amalni tanlang:",
        reply_markup=kb.users_list_keyboard(users),
    )


async def user_detail(update, context, user_id: int):
    user = db.get_user_by_id(user_id)
    if not user:
        await _edit(update, "❌ User topilmadi.", kb.back_button("user_list"))
        return
    status = "ro'yxatdan o'tgan" if user["registered"] else "kutilmoqda"
    text = (
        f"👤 {user['name']}\n"
        f"🔑 Login: {user['login']}\n"
        f"🎚 Rol: {user['role']}\n"
        f"📊 Holat: {status}\n"
        f"🆔 Telegram ID: {user['telegram_id'] or '-'}"
    )
    await _edit(update, text, kb.user_detail_keyboard(user_id))


async def user_edit_start(update, context, user_id: int, field: str):
    flows = {
        "name": "edit_name",
        "login": "edit_login",
        "password": "edit_pass",
    }
    context.user_data["flow"] = flows[field]
    context.user_data["edit_user_id"] = user_id
    labels = {
        "name": "Yangi ismni kiriting:",
        "login": "Yangi login kiriting:",
        "password": "Yangi parol kiriting:",
    }
    await _edit(update, labels[field])


async def edit_name_text(update, context):
    uid = context.user_data.get("edit_user_id")
    db.update_user(uid, name=update.message.text.strip())
    await _finish_edit(update, context, uid, "Ism o'zgartirildi")


async def edit_login_text(update, context):
    uid = context.user_data.get("edit_user_id")
    login = update.message.text.strip()
    existing = db.get_user_by_login(login)
    if existing and existing["id"] != uid:
        await update.message.reply_text("❌ Bunday login bor. Boshqa login kiriting:")
        return
    db.update_user(uid, login=login)
    await _finish_edit(update, context, uid, "Login o'zgartirildi")


async def edit_pass_text(update, context):
    uid = context.user_data.get("edit_user_id")
    db.update_user(uid, password=update.message.text.strip())
    await _finish_edit(update, context, uid, "Parol o'zgartirildi")


async def _finish_edit(update, context, user_id, message):
    context.user_data["flow"] = None
    context.user_data.pop("edit_user_id", None)
    await update.message.reply_text(f"✅ {message}.")
    user = db.get_user_by_id(user_id)
    status = "ro'yxatdan o'tgan" if user["registered"] else "kutilmoqda"
    await update.message.reply_text(
        f"👤 {user['name']}\n🔑 Login: {user['login']}\n📊 Holat: {status}",
        reply_markup=kb.user_detail_keyboard(user_id),
    )


async def user_delete_confirm(update, context, user_id: int):
    from ..keyboards import confirm_keyboard

    user = db.get_user_by_id(user_id)
    await _edit(
        update,
        f"❗ {user['name']} ni o'chirishni tasdiqlaysizmi?",
        confirm_keyboard(f"udel_yes:{user_id}", "user_list"),
    )


async def user_delete(update, context, user_id: int):
    db.delete_user(user_id)
    await users_list(update, context)


async def flow_cancel(update, context):
    context.user_data["flow"] = None
    context.user_data.pop("new_arena", None)
    context.user_data.pop("new_q", None)
    context.user_data.pop("new_user", None)
    context.user_data.pop("reg", None)
    context.user_data.pop("edit_user_id", None)
    if _admin(update):
        await _edit(update, "❌ Amal bekor qilindi.", kb.admin_menu())
    else:
        await _edit(update, "❌ Amal bekor qilindi. /start buyrug'ini qayta bosing.")
