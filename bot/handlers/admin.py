"""Admin panel: English arena boshqaruvi va Userlar boshqaruvi."""

from telegram import InlineKeyboardMarkup

import csv
import io

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
        await _edit(update, "в›” Bu bo'lim faqat admin uchun.")
        return
    context.user_data["flow"] = None
    await _edit(
        update,
        "рџ‘‘ ADMIN PANEL\n\nBoshqaruv bo'limini tanlang:",
        kb.admin_menu(),
    )


async def arena_manage(update, context):
    if not _admin(update):
        return
    context.user_data["flow"] = None
    await _edit(update, "рџЏџ ENGLISH ARENA BOSHQARUVI", kb.arena_manage_menu())


async def users_manage(update, context):
    if not _admin(update):
        return
    context.user_data["flow"] = None
    await _edit(update, "рџ‘Ґ USERLAR BOSHQARUVI", kb.users_manage_menu())


def _fmt_percent(value):
    if value is None:
        return "0"
    return f"{float(value):g}"


async def admin_stats(update, context):
    if not _admin(update):
        return
    stats = db.get_admin_stats()
    lines = [
        "рџ“Љ BOT STATISTIKASI\n",
        f"рџ‘Ґ Userlar: {stats.get('users_count', 0)} (ro'yxatdan o'tgan: {stats.get('registered_count', 0)})",
        f"рџЏџ Arenalar: {stats.get('arenas_count', 0)} (ochiq: {stats.get('open_arenas_count', 0)})",
        f"вќ“ Savollar: {stats.get('questions_count', 0)}",
        f"рџ“ќ Natijalar: {stats.get('results_count', 0)}",
        f"рџ“€ O'rtacha foiz: {_fmt_percent(stats.get('avg_percent'))}%",
    ]
    top_arenas = stats.get("top_arenas") or []
    if top_arenas:
        lines.append("\nTop arenalar:")
        for a in top_arenas:
            lines.append(
                f"вЂў {a['title']} ({a['level']}) вЂ” {a['attempts']} urinish, o'rtacha {_fmt_percent(a['avg_percent'])}%"
            )
    hardest = stats.get("hardest_questions") or []
    if hardest:
        lines.append("\nEng qiyin savollar:")
        for q in hardest:
            lines.append(
                f"вЂў {q['uz_word']} в†’ {q['en_word']} ({q.get('arena_title','-')}) вЂ” "
                f"xato {_fmt_percent(q.get('wrong_percent'))}% ({q.get('wrong_count',0)}/{q.get('attempt_count',0)})"
            )
    await _edit(update, "\n".join(lines), kb.admin_menu())


async def admin_export_results(update, context):
    if not _admin(update):
        return
    rows = db.list_all_results()
    if not rows:
        await _edit(update, "вќЊ Hali natijalar yo'q.", kb.admin_menu())
        return

    output = io.StringIO()
    fieldnames = ["completed_at", "user_name", "user_login", "arena_title", "arena_level", "score", "max_score", "percentage", "medal"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fieldnames})

    data = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    await update.callback_query.message.reply_document(
        document=data,
        filename="results_export.csv",
        caption=f"рџ“Ґ Natijalar eksporti: {len(rows)} ta",
    )
    await _edit(update, f"вњ… Natijalar CSV tayyor: {len(rows)} ta.", kb.admin_menu())


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
        f"вњ… Arena yaratildi:\n\nрџЏџ {arena['title']}\nрџ“ќ {arena['description']}\nрџЋљ Daraja: {arena['level']}",
        kb.arena_detail_keyboard(arena),
    )


# =========================================================================== #
# Arenalar ro'yxati va detail
# =========================================================================== #
async def arenas_list(update, context):
    arenas = db.list_arenas()
    text = "рџ“‹ ARENALAR RO'YXATI\n\n" if arenas else "рџ“‹ Hali arena yo'q."
    await _edit(update, text + "Arenani tanlang:", kb.arenas_list_keyboard(arenas))


async def arena_detail(update, context, arena_id: int):
    arena = db.get_arena(arena_id)
    if not arena:
        await _edit(update, "вќЊ Arena topilmadi.", kb.back_button("arena_list"))
        return
    count = len(db.list_questions(arena_id))
    status = "рџџў OCHIQ" if arena["is_open"] else "рџ”ґ YOPIQ"
    text = (
        f"рџЏџ {arena['title']}\n"
        f"рџ“ќ {arena['description']}\n"
        f"рџЋљ Daraja: {arena['level']} ({db_level_points(arena['level'])} achko/savol)\n"
        f"рџ“Љ Holat: {status}\n"
        f"вќ“ Savollar soni: {count}"
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
        "вќ— Arenani o'chirishni tasdiqlaysizmi? Unga tegishli barcha savollar ham o'chadi.",
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
        "vocab": "📖 O'zbekcha so'zni kiriting:",
        "definition": "📘 Inglizcha ta'rifni kiriting:",
        "gap": "✏️ Nuqtali gapni yozing (masalan: I ___ to school.):",
        "idiom": "💬 Idiomni kiriting (masalan: At all costs):",
    }
    await _edit(update, prompts.get(qtype, prompts["vocab"]))


async def q_uz_text(update, context):
    context.user_data["new_q"]["uz"] = update.message.text.strip()
    context.user_data["flow"] = "q_en"
    qtype = context.user_data["new_q"].get("qtype", "vocab")
    prompts = {
        "vocab": "Inglizcha to'g'ri javobni kiriting:",
        "definition": "Ta'rifga mos inglizcha so'zni kiriting:",
        "gap": "Nuqta o'rniga keladigan so'zni kiriting:",
        "idiom": "Idiom o'zini kiriting (typing bosqichi uchun):",
    }
    await update.message.reply_text(prompts.get(qtype, prompts["vocab"]))


def _option_prompt(qtype: str, letter: str) -> str:
    if qtype == "idiom":
        suffix = " (ma'no/definition)"
    elif qtype == "definition":
        suffix = " (so'z)"
    else:
        suffix = ""
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
        await _edit(update, "вќЊ Savol qo'shish jarayoni tugagan.", kb.back_button("arena_list"))
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


async def questions_list(update, context, arena_id: int, delete_mode=False, page=0):
    questions = db.list_questions(arena_id)
    if not questions:
        await _edit(
            update,
            "вќЊ Bu arenada savol yo'q.",
            kb.back_button(f"arena:{arena_id}"),
        )
        return
    per_page = 10
    total_pages = max(1, (len(questions) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    chunk = questions[start:start + per_page]
    title = "рџ—‘ SAVOL O'CHIRISH" if delete_mode else "рџ“‹ SAVOLLAR RO'YXATI"
    arena = db.get_arena(arena_id)
    arena_title = arena["title"] if arena else "Arena"
    text = (
        f"{title}\n"
        f"Arena: {arena_title}\n"
        f"Jami: {len(questions)} ta | Sahifa: {page + 1}/{total_pages}\n\n"
        "Savolni tanlang:"
    )
    await _edit(update, text, kb.questions_keyboard(chunk, arena_id, delete_mode, page, total_pages))


async def question_search_start(update, context, arena_id: int):
    if not _admin(update):
        return
    context.user_data["flow"] = "q_search"
    context.user_data["search_arena_id"] = arena_id
    await _edit(update, "рџ”Ќ Qidirish uchun so'z yoki ibora yozing:\n\nBekor qilish uchun /cancel yozing.")


async def q_search_text(update, context):
    if not _admin(update):
        return
    arena_id = context.user_data.get("search_arena_id")
    query = (update.message.text or "").strip()
    if query.lower() in ("/cancel", "bekor"):
        context.user_data["flow"] = None
        context.user_data.pop("search_arena_id", None)
        await update.message.reply_text("вќЊ Qidiruv bekor qilindi.")
        return
    if not arena_id or not query:
        await update.message.reply_text("вќЊ Qidiruv so'zini kiriting.")
        return
    results = db.search_questions(arena_id, query, limit=20)
    context.user_data["flow"] = None
    context.user_data.pop("search_arena_id", None)
    if not results:
        await update.message.reply_text(
            f"рџ”Ќ \"{query}\" bo'yicha hech narsa topilmadi.",
            reply_markup=kb.back_button(f"arena:{arena_id}"),
        )
        return
    text = f"рџ”Ќ \"{query}\" bo'yicha natijalar: {len(results)} ta\n\nSavolni tanlang:"
    await update.message.reply_text(
        text,
        reply_markup=kb.questions_keyboard(results, arena_id, delete_mode=False),
    )


async def question_info(update, context, question_id: int, arena_id: int):
    q = db.get_question(question_id)
    if not q:
        await _edit(update, "вќЊ Savol topilmadi.", kb.back_button(f"arena:{arena_id}"))
        return
    qtype = q.get("question_type", "vocab")
    labels = {
        "gap": ("Gap to'ldirish (gap filling)", "Gap"),
        "definition": ("Definition → Word", "Ta'rif"),
        "idiom": ("Idiom (definition + tarjima)", "Idiom"),
    }
    qtype_label, word_label = labels.get(qtype, ("Lug'at so'zi", "O'zbekcha"))
    text = (
        f"вќ“ Savol #{q['id']}\n"
        f"рџЏ· Turi: {qtype_label}\n\n"
        f"{word_label}: {q['uz_word']}\n"
        f"To'g'ri javob: {q['en_word']}\n\n"
        f"a) {q['opt_a']}\n"
        f"b) {q['opt_b']}\n"
        f"c) {q['opt_c']}\n"
        f"d) {q['opt_d']}\n\n"
        f"вњ… To'g'ri variant: {q['correct'].upper()}"
    )
    if qtype == "idiom":
        info = get_idiom_info(q["en_word"]) or {}
        text += (
            f"\n\nрџ“– Definition: {info.get('definition', '-')}"
            f"\nрџ‡єрџ‡ї Tarjima: {info.get('uzbek', '-')}"
        )
    await _edit(update, text, kb.question_info_keyboard(question_id, arena_id))


async def question_delete(update, context, question_id: int, arena_id: int):
    db.delete_question(question_id)
    await questions_list(update, context, arena_id, delete_mode=True)


# --------------------------------------------------------------------------- #
# Savol tahrirlash
# --------------------------------------------------------------------------- #
_EDIT_FIELD_MAP = {
    "uz": "uz_word",
    "en": "en_word",
    "a": "opt_a",
    "b": "opt_b",
    "c": "opt_c",
    "d": "opt_d",
    "correct": "correct",
}


async def question_edit_menu(update, context, question_id: int, arena_id: int):
    q = db.get_question(question_id)
    if not q:
        await _edit(update, "вќЊ Savol topilmadi.", kb.back_button(f"qlist:{arena_id}"))
        return
    await _edit(
        update,
        f"вњЏпёЏ SAVOLNI TAHRIRLASH\n\n{q['uz_word']} в†’ {q['en_word']}\n\nQaysi maydonni o'zgartirasiz?",
        kb.question_edit_keyboard(question_id, arena_id),
    )


async def question_edit_field_start(update, context, question_id: int, arena_id: int, field: str):
    q = db.get_question(question_id)
    if not q:
        await _edit(update, "вќЊ Savol topilmadi.", kb.back_button(f"qlist:{arena_id}"))
        return
    if field == "correct":
        await _edit(
            update,
            f"To'g'ri javob harfini tanlang (hozirgi: {q['correct'].upper()}):",
            kb.question_edit_correct_keyboard(question_id, arena_id),
        )
        return

    context.user_data["edit_q"] = {"question_id": question_id, "arena_id": arena_id, "field": field}
    context.user_data["flow"] = "qe_text"
    qtype = q.get("question_type", "vocab")
    prompts = {
        "uz": {
            "vocab": "Yangi o'zbekcha so'zni kiriting:",
            "definition": "Yangi inglizcha ta'rifni kiriting:",
            "gap": "Yangi nuqtali gapni kiriting:",
            "idiom": "Yangi idiomni kiriting:",
        },
        "en": {
            "vocab": "Yangi inglizcha javobni kiriting:",
            "definition": "Yangi inglizcha so'zni kiriting:",
            "gap": "Yangi nuqta o'rniga keladigan so'zni kiriting:",
            "idiom": "Yangi idiom so'zini kiriting (typing bosqichi uchun):",
        },
        "a": {"_": "Yangi A variantni kiriting:"},
        "b": {"_": "Yangi B variantni kiriting:"},
        "c": {"_": "Yangi C variantni kiriting:"},
        "d": {"_": "Yangi D variantni kiriting:"},
    }
    by_type = prompts.get(field, {"_": "Yangi qiymatni kiriting:"})
    prompt = by_type.get(qtype) or by_type.get("_") or "Yangi qiymatni kiriting:"
    current = q.get(_EDIT_FIELD_MAP[field], "")
    await _edit(update, f"{prompt}\n\nHozirgi: {current}")


async def qe_text(update, context):
    data = context.user_data.get("edit_q") or {}
    qid, aid, field = data.get("question_id"), data.get("arena_id"), data.get("field")
    if not qid or not field:
        context.user_data["flow"] = None
        await update.message.reply_text("вќЊ Tahrirlash jarayoni topilmadi.")
        return
    db_field = _EDIT_FIELD_MAP.get(field)
    value = (update.message.text or "").strip()
    if not value or not db_field:
        await update.message.reply_text("вќЊ Qiymat bo'sh bo'lmasin.")
        return
    db.update_question(qid, **{db_field: value})
    context.user_data["flow"] = None
    context.user_data.pop("edit_q", None)
    await update.message.reply_text("вњ… Saqlandi.")
    # show updated question info
    q = db.get_question(qid)
    if not q:
        await update.message.reply_text("вќЊ Savol topilmadi.")
        return
    # reuse question_info rendering by sending a fake update-like message? easier to build text
    text = (
        f"рџ“‹ SAVOL\n\n"
        f"рџ“ќ {q['uz_word']}\n"
        f"рџ‡¬рџ‡§ {q['en_word']}\n\n"
        f"A) {q['opt_a']}\nB) {q['opt_b']}\nC) {q['opt_c']}\nD) {q['opt_d']}\n\n"
        f"вњ… To'g'ri javob: {q['correct'].upper()}\n"
        f"Turi: {q.get('question_type', 'vocab')}"
    )
    qtype = q.get("question_type", "vocab")
    if qtype == "idiom":
        info = get_idiom_info(q["en_word"]) or {}
        text += (
            f"\n\nрџ“– Definition: {info.get('definition', '-')}"
            f"\nрџ‡єрџ‡ї Tarjima: {info.get('uzbek', '-')}"
        )
    await update.message.reply_text(text, reply_markup=kb.question_info_keyboard(qid, aid))


async def question_edit_correct(update, context, question_id: int, arena_id: int, letter: str):
    db.update_question(question_id, correct=letter)
    await question_info(update, context, question_id, arena_id)


async def questions_export(update, context, arena_id: int):
    if not _admin(update):
        return
    arena = db.get_arena(arena_id)
    questions = db.list_questions(arena_id)
    if not questions:
        await _edit(update, "вќЊ Bu arenada eksport qilish uchun savol yo'q.", kb.back_button(f"arena:{arena_id}"))
        return

    output = io.StringIO()
    fieldnames = ["uz_word", "en_word", "opt_a", "opt_b", "opt_c", "opt_d", "correct", "question_type"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for q in questions:
        writer.writerow({k: q.get(k, "") for k in fieldnames})

    data = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    name = f"arena_{arena_id}_questions.csv"
    caption = f"рџ“¤ {arena['title'] if arena else 'Arena'} вЂ” {len(questions)} ta savol"
    await update.callback_query.message.reply_document(document=data, filename=name, caption=caption)
    await _edit(update, f"вњ… CSV eksport tayyor: {len(questions)} ta savol.", kb.back_button(f"arena:{arena_id}"))


async def question_import_start(update, context, arena_id: int):
    if not _admin(update):
        return
    context.user_data["flow"] = "q_import_csv"
    context.user_data["import_arena_id"] = arena_id
    await _edit(
        update,
        "рџ“Ґ CSV IMPORT\n\n"
        "CSV fayl yuboring. Ustunlar:\n"
        "uz_word,en_word,opt_a,opt_b,opt_c,opt_d,correct,question_type\n\n"
        "correct: a/b/c/d\n"
        "question_type: vocab/gap/idiom (bo'sh bo'lsa vocab)\n\n"
        "Bekor qilish uchun /cancel yozing.",
    )


async def question_import_document(update, context):
    if not _admin(update):
        return
    if context.user_data.get("flow") != "q_import_csv":
        return
    arena_id = context.user_data.get("import_arena_id")
    doc = update.message.document
    if not doc:
        await update.message.reply_text("вќЊ CSV fayl yuboring.")
        return
    if not (doc.file_name or "").lower().endswith(".csv"):
        await update.message.reply_text("вќЊ Faqat .csv fayl yuboring.")
        return

    tg_file = await doc.get_file()
    raw = await tg_file.download_as_bytearray()
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    required = {"uz_word", "en_word", "opt_a", "opt_b", "opt_c", "opt_d", "correct"}
    fields = set(reader.fieldnames or [])
    if not required.issubset(fields):
        await update.message.reply_text(
            "вќЊ CSV ustunlari noto'g'ri. Kerak: uz_word,en_word,opt_a,opt_b,opt_c,opt_d,correct,question_type"
        )
        return

    added = 0
    skipped = 0
    for row in reader:
        uz = (row.get("uz_word") or "").strip()
        en = (row.get("en_word") or "").strip()
        opts = [(row.get(k) or "").strip() for k in ("opt_a", "opt_b", "opt_c", "opt_d")]
        correct = (row.get("correct") or "").strip().lower()
        qtype = (row.get("question_type") or "vocab").strip().lower() or "vocab"
        if not uz or not en or not all(opts) or correct not in "abcd":
            skipped += 1
            continue
        if qtype not in {"vocab", "gap", "idiom", "definition"}:
            qtype = "vocab"
        db.add_question(arena_id, uz, en, *opts, correct, qtype)
        added += 1

    context.user_data["flow"] = None
    context.user_data.pop("import_arena_id", None)
    arena = db.get_arena(arena_id) if arena_id else None
    msg = f"вњ… Import tugadi. Qo'shildi: {added} ta"
    if skipped:
        msg += f", o'tkazildi: {skipped} ta"
    if arena:
        msg += f"\n\nрџЏџ {arena['title']}\nвќ“ Jami savollar: {len(db.list_questions(arena_id))}"
        await update.message.reply_text(msg, reply_markup=kb.arena_detail_keyboard(arena))
    else:
        await update.message.reply_text(msg)


# =========================================================================== #
# AI orqali lug'at qo'shish
# =========================================================================== #
AI_LABELS = {
    "vocab": ("avlvl", "рџ¤– AI lug'at qo'shish", "lug'at"),
    "gap": ("agvlvl", "рџ¤– AI gap-fill qo'shish", "gap-fill"),
    "idiom": ("aidlvl", "рџ¤– AI idiom qo'shish", "idiom"),
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
    extra = "\nрџ’¬ To'g'ri idiom javobi har bosqichda 3 achko beradi." if qtype == "idiom" else ""
    await _edit(
        update,
        f"вњ… {level} darajasi uchun {added} ta {label} savoli qo'shildi.{extra}\n\n"
        f"рџЏџ {arena['title']}\nвќ“ Jami savollar: {len(db.list_questions(arena_id))}",
        kb.arena_detail_keyboard(arena),
    )


# =========================================================================== #
# Userlar boshqaruvi
# =========================================================================== #
async def users_list(update, context, page=0):
    users = db.list_users()
    if not users:
        await _edit(update, "рџ‘Ґ Hali user yo'q.", kb.users_list_keyboard([]))
        return
    per_page = 10
    total_pages = max(1, (len(users) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    chunk = users[start:start + per_page]
    text = f"рџ‘Ґ USERLAR RO'YXATI\nJami: {len(users)} ta | Sahifa: {page + 1}/{total_pages}\n\nUser yoki amalni tanlang:"
    await _edit(update, text, kb.users_list_keyboard(chunk, page, total_pages))


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
        await update.message.reply_text("вќЊ Bunday login bor. Boshqa login kiriting:")
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
        f"вњ… User yaratildi:\n\nрџ‘¤ {user['name']}\nрџ”‘ Login: {user['login']}\n"
        f"рџ”’ Parol: {password}\n\n"
        "Endi bu login va parol bilan botda ro'yxatdan o'tish mumkin."
    )
    await users_list_from_message(update, context)


async def users_list_from_message(update, context):
    # Yangi user yaratilgandan keyin ro'yxatni yangi xabar bilan ko'rsatish
    users = db.list_users()
    await update.message.reply_text(
        "рџ‘Ґ USERLAR RO'YXATI\n\nUser yoki amalni tanlang:",
        reply_markup=kb.users_list_keyboard(users),
    )


async def user_detail(update, context, user_id: int):
    user = db.get_user_by_id(user_id)
    if not user:
        await _edit(update, "вќЊ User topilmadi.", kb.back_button("user_list"))
        return
    status = "ro'yxatdan o'tgan" if user["registered"] else "kutilmoqda"
    text = (
        f"рџ‘¤ {user['name']}\n"
        f"рџ”‘ Login: {user['login']}\n"
        f"рџЋљ Rol: {user['role']}\n"
        f"рџ“Љ Holat: {status}\n"
        f"рџ†” Telegram ID: {user['telegram_id'] or '-'}"
    )
    await _edit(update, text, kb.user_detail_keyboard(user_id))


async def user_results(update, context, user_id: int):
    if not _admin(update):
        return
    user = db.get_user_by_id(user_id)
    if not user:
        await _edit(update, "вќЊ User topilmadi.", kb.back_button("user_list"))
        return
    stats = db.get_user_stats(user_id) or {}
    rows = db.list_user_results(user_id, limit=10)
    lines = [
        f"рџ“Љ {user['name']} вЂ” natijalar\n",
        f"Urinishlar: {stats.get('attempts', 0)}",
        f"O'rtacha: {_fmt_percent(stats.get('avg_percent'))}%",
        f"Eng yaxshi: {_fmt_percent(stats.get('best_percent'))}%",
        f"Jami achko: {stats.get('total_score') or 0}",
    ]
    if rows:
        lines.append("\nSo'nggi natijalar:")
        for r in rows:
            arena = r.get("arena_title") or "Arena"
            level = r.get("arena_level") or "-"
            lines.append(
                f"вЂў {arena} ({level}) вЂ” {r['score']}/{r['max_score']} ({_fmt_percent(r['percentage'])}%) {r['medal']}"
            )
    else:
        lines.append("\nHali natija yo'q.")
    await _edit(update, "\n".join(lines), kb.back_button(f"udetail:{user_id}"))


async def user_results_export(update, context, user_id: int):
    if not _admin(update):
        return
    user = db.get_user_by_id(user_id)
    if not user:
        await _edit(update, "вќЊ User topilmadi.", kb.back_button("user_list"))
        return
    rows = db.list_user_results(user_id, limit=5000)
    if not rows:
        await _edit(update, "вќЊ Bu userda natijalar yo'q.", kb.back_button(f"udetail:{user_id}"))
        return
    output = io.StringIO()
    fieldnames = ["completed_at", "arena_title", "arena_level", "score", "max_score", "percentage", "medal"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fieldnames})
    data = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    await update.callback_query.message.reply_document(
        document=data,
        filename=f"user_{user_id}_results.csv",
        caption=f"рџ“Ґ {user['name']} natijalari: {len(rows)} ta",
    )
    await _edit(update, f"вњ… {user['name']} natijalari CSV tayyor: {len(rows)} ta.", kb.back_button(f"udetail:{user_id}"))


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
        await update.message.reply_text("вќЊ Bunday login bor. Boshqa login kiriting:")
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
    await update.message.reply_text(f"вњ… {message}.")
    user = db.get_user_by_id(user_id)
    status = "ro'yxatdan o'tgan" if user["registered"] else "kutilmoqda"
    await update.message.reply_text(
        f"рџ‘¤ {user['name']}\nрџ”‘ Login: {user['login']}\nрџ“Љ Holat: {status}",
        reply_markup=kb.user_detail_keyboard(user_id),
    )


async def user_delete_confirm(update, context, user_id: int):
    from ..keyboards import confirm_keyboard

    user = db.get_user_by_id(user_id)
    await _edit(
        update,
        f"вќ— {user['name']} ni o'chirishni tasdiqlaysizmi?",
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
        await _edit(update, "вќЊ Amal bekor qilindi.", kb.admin_menu())
    else:
        await _edit(update, "вќЊ Amal bekor qilindi. /start buyrug'ini qayta bosing.")

# =========================================================================== #
# Kitobdan savol qo'shish
# =========================================================================== #
async def book_source_start(update, context, arena_id: int):
    from ..books import list_books

    context.user_data["flow"] = None
    context.user_data.pop("new_q", None)
    books = list_books()
    if not books:
        await _edit(update, "рџ“љ Hozircha kitoblar yo'q.", kb.back_button(f"arena:{arena_id}"))
        return
    await _edit(
        update,
        "рџ“љ Kitobdan qo'shish\n\nKitobni tanlang:",
        kb.books_keyboard(books, arena_id),
    )


async def book_units(update, context, book_id: str, arena_id: int, page: int = 0):
    from ..books import get_book

    book = get_book(book_id)
    if not book:
        await _edit(update, "вќЊ Kitob topilmadi.", kb.back_button(f"arena:{arena_id}"))
        return
    units = book.get("units", [])
    await _edit(
        update,
        f"рџ“љ {book['title']}\n\nUnitni tanlang:",
        kb.book_units_keyboard(book_id, units, arena_id, page=page),
    )


async def book_unit_types(update, context, book_id: str, unit: int, arena_id: int):
    from ..books import get_book, available_question_types

    book = get_book(book_id)
    if not book:
        await _edit(update, "вќЊ Kitob topilmadi.", kb.back_button(f"arena:{arena_id}"))
        return
    types = available_question_types(book_id, unit)
    await _edit(
        update,
        f"рџ“љ {book['title']} вЂ” Unit {unit}\n\nQaysi turdagi savollar qo'shilsin?",
        kb.book_qtype_keyboard(book_id, unit, arena_id, types),
    )


async def book_apply(update, context, book_id: str, unit: int, qtype: str, arena_id: int):
    from ..books import get_book, build_question_items

    book = get_book(book_id)
    if not book:
        await _edit(update, "вќЊ Kitob topilmadi.", kb.back_button(f"arena:{arena_id}"))
        return

    items = build_question_items(book_id, unit, qtype)
    if not items:
        from ..books import available_question_types
        types = available_question_types(book_id, unit)
        await _edit(
            update,
            f"❌ {book['title']} Unit {unit} uchun '{qtype}' turida savol yaratib bo'lmadi.\n"
            "Ehtimol bu unitda ta'rif/misol yetarli emas.",
            kb.book_qtype_keyboard(book_id, unit, arena_id, types),
        )
        return

    added = db.add_questions_bulk(arena_id, items, qtype)
    arena = db.get_arena(arena_id)
    labels = {
        "vocab": "lug'at",
        "definition": "definitionв†’word",
        "gap": "gap-fill",
    }
    label = labels.get(qtype, qtype)
    await _edit(
        update,
        f"вњ… {book['short']} Unit {unit} dan {added} ta {label} savol qo'shildi.\n\n"
        f"рџЏџ {arena['title']}\nрџ“‹ Jami savollar: {len(db.list_questions(arena_id))}",
        kb.arena_detail_keyboard(arena),
    )
