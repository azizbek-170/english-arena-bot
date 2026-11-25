"""Barcha tugmalar (reply + inline) shu yerda yig'iladi."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from .config import LEVELS

BTN_ADMIN = "Admin panel"
BTN_ENGLISH = "Ingiliz tili arenasi"
BTN_LOGIN = "🔑 Login bilan kirish"


def cb(*parts) -> str:
    """Callback data yasash (telegram 64 bayt chekloviga rioya qilinadi)."""
    return ":".join(str(p) for p in parts)


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [[BTN_ENGLISH]]
    if is_admin:
        rows.append([BTN_ADMIN])
    else:
        # Eski admin bergan login/parol bilan kirish uchun (asosiy usul avtomatik)
        rows.append([BTN_LOGIN])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def confirm_keyboard(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Ha", callback_data=yes_data),
                InlineKeyboardButton("❌ Yo'q", callback_data=no_data),
            ]
        ]
    )


def back_button(data: str = "back_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data=data)]])


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏟 English arena boshqaruvi", callback_data="adm_arenas")],
            [InlineKeyboardButton("👥 Userlar boshqaruvi", callback_data="adm_users")],
            [InlineKeyboardButton("📊 Statistika", callback_data="adm_stats")],
            [InlineKeyboardButton("📥 Natijalar CSV", callback_data="adm_export_results")],
            [InlineKeyboardButton("⬅️ Asosiy menyu", callback_data="back_main")],
        ]
    )


def arena_manage_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Arena qo'shish", callback_data="arena_add")],
            [InlineKeyboardButton("📋 Arenalar ro'yxati", callback_data="arena_list")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="adm_menu")],
        ]
    )


def users_manage_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 Userlar ro'yxati", callback_data="user_list")],
            [InlineKeyboardButton("➕ Yangi user qo'shish", callback_data="user_add")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="adm_menu")],
        ]
    )


def arenas_list_keyboard(arenas, back="arena_manage") -> InlineKeyboardMarkup:
    rows = []
    for arena in arenas:
        icon = "🟢" if arena["is_open"] else "🔴"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{icon} {arena['title']} ({arena['level']})",
                    callback_data=cb("arena", arena["id"]),
                )
            ]
        )
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data=back)])
    return InlineKeyboardMarkup(rows)


def open_arenas_keyboard(arenas) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                f"🎯 {arena['title']} · {arena['level']}",
                callback_data=cb("play", arena["id"]),
            )
        ]
        for arena in arenas
    ]
    rows.append(
        [
            InlineKeyboardButton("📊 Natijalarim", callback_data="my_results"),
            InlineKeyboardButton("🏆 Reyting", callback_data="leaderboard"),
        ]
    )
    rows.append([InlineKeyboardButton("⬅️ Asosiy menyu", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def arena_detail_keyboard(arena) -> InlineKeyboardMarkup:
    aid = arena["id"]
    status_text = "🔒 Arenani yopish" if arena["is_open"] else "🔓 Arenani ochish"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(status_text, callback_data=cb("atoggle", aid))],
            [
                InlineKeyboardButton("➕ Savol qo'shish", callback_data=cb("qadd", aid)),
                InlineKeyboardButton("🤖 AI lug'at qo'shish", callback_data=cb("aivocab", aid)),
            ],
            [InlineKeyboardButton("🤖 AI gap-fill qo'shish", callback_data=cb("aigap", aid))],
            [InlineKeyboardButton("🤖 AI idiom qo'shish", callback_data=cb("aiidiom", aid))],
            [
                InlineKeyboardButton("📋 Savollar ro'yxati", callback_data=cb("qlist", aid)),
                InlineKeyboardButton("🗑 Savol o'chirish", callback_data=cb("qdelmode", aid)),
            ],
            [
                InlineKeyboardButton("📤 CSV eksport", callback_data=cb("qexport", aid)),
                InlineKeyboardButton("📥 CSV import", callback_data=cb("qimport", aid)),
            ],
            [InlineKeyboardButton("🗑 Arenani o'chirish", callback_data=cb("adel", aid))],
            [InlineKeyboardButton("⬅️ Arenalar ro'yxati", callback_data="arena_list")],
        ]
    )


def question_type_keyboard(arena_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📖 Lug'at so'zi (O'zbekcha → Inglizcha)", callback_data=cb("qtype", "vocab", arena_id))],
            [InlineKeyboardButton("✏️ Gap to'ldirish (gap filling)", callback_data=cb("qtype", "gap", arena_id))],
            [InlineKeyboardButton("💬 Idiom (definition + tarjima)", callback_data=cb("qtype", "idiom", arena_id))],
            [InlineKeyboardButton("⬅️ Bekor qilish", callback_data=cb("arena", arena_id))],
        ]
    )


def levels_keyboard(prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(level, callback_data=cb(prefix, level)) for level in LEVELS]]
    rows.append([InlineKeyboardButton("⬅️ Bekor qilish", callback_data="flow_cancel")])
    return InlineKeyboardMarkup(rows)


def letters_keyboard(prefix: str, arena_id=None) -> InlineKeyboardMarkup:
    parts = [prefix] + ([arena_id] if arena_id is not None else [])
    rows = [
        [
            InlineKeyboardButton(letter.upper(), callback_data=cb(*parts, letter))
            for letter in "abcd"
        ]
    ]
    rows.append([InlineKeyboardButton("⬅️ Bekor qilish", callback_data="flow_cancel")])
    return InlineKeyboardMarkup(rows)


def questions_keyboard(questions, arena_id: int, delete_mode=False, page=0, total_pages=1) -> InlineKeyboardMarkup:
    rows = []
    for q in questions:
        prefix = "qdel" if delete_mode else "qinfo"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{q['uz_word']} → {q['en_word']}",
                    callback_data=cb(prefix, q["id"], arena_id),
                )
            ]
        )
    if total_pages > 1:
        nav = []
        list_prefix = "qdelmode" if delete_mode else "qlist"
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=cb(list_prefix, arena_id, page - 1)))
        nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("➡️", callback_data=cb(list_prefix, arena_id, page + 1)))
        rows.append(nav)
    rows.append(
        [InlineKeyboardButton("⬅️ Arenaga qaytish", callback_data=cb("arena", arena_id))]
    )
    return InlineKeyboardMarkup(rows)


def question_info_keyboard(question_id: int, arena_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✏️ Tahrirlash", callback_data=cb("qedit", question_id, arena_id))],
            [InlineKeyboardButton("⬅️ Savollar ro'yxati", callback_data=cb("qlist", arena_id))],
        ]
    )


def question_edit_keyboard(question_id: int, arena_id: int) -> InlineKeyboardMarkup:
    qid, aid = question_id, arena_id
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Savol/gap/idiom matni", callback_data=cb("qef", qid, aid, "uz"))],
            [InlineKeyboardButton("Javob/idiom so'zi", callback_data=cb("qef", qid, aid, "en"))],
            [
                InlineKeyboardButton("A", callback_data=cb("qef", qid, aid, "a")),
                InlineKeyboardButton("B", callback_data=cb("qef", qid, aid, "b")),
                InlineKeyboardButton("C", callback_data=cb("qef", qid, aid, "c")),
                InlineKeyboardButton("D", callback_data=cb("qef", qid, aid, "d")),
            ],
            [InlineKeyboardButton("To'g'ri javob harfi", callback_data=cb("qef", qid, aid, "correct"))],
            [InlineKeyboardButton("⬅️ Savolga qaytish", callback_data=cb("qinfo", qid, aid))],
        ]
    )


def question_edit_correct_keyboard(question_id: int, arena_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(letter.upper(), callback_data=cb("qecorr", question_id, arena_id, letter))
                for letter in "abcd"
            ]
        ]
    )


def users_list_keyboard(users, page=0, total_pages=1) -> InlineKeyboardMarkup:
    rows = []
    for user in users:
        icon = "👑" if user["role"] == "admin" else "👤"
        status = "✅" if user["registered"] else "⏳"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{icon} {user['name']} ({user['login']}) {status}",
                    callback_data=cb("udetail", user["id"]),
                )
            ]
        )
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=cb("user_list", page - 1)))
        nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("➡️", callback_data=cb("user_list", page + 1)))
        rows.append(nav)
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="adm_users")])
    return InlineKeyboardMarkup(rows)


def user_detail_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 Natijalar", callback_data=cb("uresults", user_id))],
            [InlineKeyboardButton("✏️ Ismni tahrirlash", callback_data=cb("uedit_name", user_id))],
            [InlineKeyboardButton("🔑 Login tahrirlash", callback_data=cb("uedit_login", user_id))],
            [InlineKeyboardButton("🔒 Parol tahrirlash", callback_data=cb("uedit_pass", user_id))],
            [InlineKeyboardButton("🗑 User o'chirish", callback_data=cb("udel", user_id))],
            [InlineKeyboardButton("⬅️ Userlar ro'yxati", callback_data="user_list")],
        ]
    )


def mcq_keyboard(question, arena_id: int) -> InlineKeyboardMarkup:
    rows = []
    for letter in "abcd":
        rows.append(
            [
                InlineKeyboardButton(
                    f"{letter.upper()}) {question[f'opt_{letter}']}",
                    callback_data=cb("qans", arena_id, question["id"], letter),
                )
            ]
        )
    rows.append([InlineKeyboardButton("❌ Chiqish", callback_data="cancel_arena_cb")])
    return InlineKeyboardMarkup(rows)
