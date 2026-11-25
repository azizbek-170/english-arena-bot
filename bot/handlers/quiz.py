"""Ingliz tili arenasi: tanlov va typing bosqichlari, ball va medallar."""

import logging
import random

from telegram.ext import ContextTypes

from .. import database as db
from .. import keyboards as kb
from ..config import LEVEL_POINTS, MEDAL_BRONZE, MEDAL_GOLD, MEDAL_SILVER
from ..utils import normalize_answer, safe_edit
from ..vocabulary import get_idiom_info
from .start import show_main

logger = logging.getLogger(__name__)


def _question_points(quiz, q) -> int:
    """Idiom savoli darajadan qat'i nazar 3 achko beradi."""
    if q.get("question_type") == "idiom":
        return 3
    return quiz["base_points"]


def _idiom_detail(q) -> str:
    """Idiom savolida definition va o'zbekcha tarjimani ko'rsatadi."""
    info = get_idiom_info(q.get("en_word", "")) or {}
    return (
        f"\n📖 Definition: {info.get('definition', '-')}"
        f"\n🇺🇿 Tarjima: {info.get('uzbek', '-')}"
    )


def _shuffle_quiz_question(q, force_letter: str = None):
    """Test boshlanishida variantlarni aralashtirib, to'g'ri harfni yangilaydi."""
    q = dict(q)
    letter = q.get("correct", "a")
    correct_text = q.get(f"opt_{letter}", "")
    opts = [q[f"opt_{l}"] for l in "abcd"]
    if correct_text not in opts:
        return q
    idx = opts.index(correct_text)
    rest = [o for i, o in enumerate(opts) if i != idx]
    random.shuffle(rest)
    pos = "abcd".index(force_letter) if force_letter in "abcd" else random.randrange(4)
    pos = min(pos, len(rest))
    for new_letter, option in zip("abcd", rest[:pos] + [correct_text] + rest[pos:]):
        q[f"opt_{new_letter}"] = option
    q["correct"] = "abcd"[pos]
    return q


async def show_english_arenas(update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user = db.get_user_by_telegram(tg_id)
    if not user or not user["registered"]:
        text = (
            "⛔ Arenaga kirish uchun ro'yxatdan o'tishingiz kerak.\n"
            "Buning uchun /start buyrug'ini bosing va loginingiz hamda parolingizni kiriting."
        )
        if update.callback_query:
            await safe_edit(update.callback_query, text)
        else:
            await update.message.reply_text(text)
        return

    arenas = db.list_open_arenas()
    text = (
        "🎯 INGLIZ TILI ARENASI\n\n"
        "Darajangizga mos arenani tanlang.\n"
        "Eslatma: xato javob berilsa achko yo'q; ketma-ket 3 xatoda -1, 5 xatoda yana -2 achko.\n\n"
    )
    if arenas:
        text += "Arenani tanlang:"
    else:
        text += "📭 Hozircha ochiq arena yo'q. Admin arenani ochishini kuting."
    markup = kb.open_arenas_keyboard(arenas)

    if update.callback_query:
        await safe_edit(update.callback_query, text, markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)


async def start_quiz(update, context: ContextTypes.DEFAULT_TYPE, arena_id: int):
    user = db.get_user_by_telegram(update.effective_user.id)
    if not user or not user["registered"]:
        await show_english_arenas(update, context)
        return

    arena = db.get_arena(arena_id)
    if not arena or not arena["is_open"]:
        await safe_edit(
            update.callback_query,
            "⛔ Arena yopiq yoki topilmadi.",
            kb.back_button("eng_arenas"),
        )
        return

    # Har safar boshqacha tartib: to'g'ri javob a/b/c/d bo'lib navbatlashadi
    offset = random.randrange(4)
    questions = [
        _shuffle_quiz_question(q, "abcd"[(i + offset) % 4])
        for i, q in enumerate(db.list_questions(arena_id))
    ]
    if not questions:
        await safe_edit(
            update.callback_query,
            "❌ Bu arenada hali savol yo'q.",
            kb.back_button("eng_arenas"),
        )
        return

    level = arena["level"]
    base_points = LEVEL_POINTS.get(level, 1)
    max_score = sum(
        (3 if q.get("question_type") == "idiom" else base_points) * 2
        for q in questions
    )
    context.user_data["quiz"] = {
        "arena_id": arena_id,
        "arena_title": arena["title"],
        "level": level,
        "points": base_points,
        "base_points": base_points,
        "questions": questions,
        "index": 0,
        "stage": "mcq",
        "score": 0,
        "streak": 0,
        "max_score": max_score,
        "user_id": user["id"],
    }
    db.save_quiz_state(update.effective_user.id, context.user_data["quiz"])
    logger.info(
        "TEST BOSHLANDI: user=%s arena=%s savollar=%s",
        user["id"], arena["title"], len(questions),
    )
    await safe_edit(update.callback_query, f"🏁 {arena['title']} boshlandi! Omad 🍀")
    await send_question(context, update.effective_chat.id)


async def send_question(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    quiz = context.user_data.get("quiz")
    if not quiz:
        return
    q = quiz["questions"][quiz["index"]]
    qtype = q.get("question_type")
    is_gap = qtype == "gap"
    is_idiom = qtype == "idiom"
    if is_idiom:
        body = f"💬 Idiom ma'nosini toping:\n{q['uz_word']}"
        action = "1-qism: idiom ma'nosini tanlang (a, b, c, d):"
    elif is_gap:
        body = f"✏️ Gapni to'ldiring:\n{q['uz_word']}"
        action = "1-qism: nuqtalar o'rniga keladigan so'zni tanlang:"
    else:
        body = f"🔤 O'zbekcha so'z: {q['uz_word']}"
        action = "1-qism: inglizcha variantni tanlang (a, b, c, d):"

    text = (
        f"📝 Savol {quiz['index'] + 1}/{len(quiz['questions'])} "
        f"· {quiz['level']} · {_question_points(quiz, q)} achko\n\n"
        f"{body}\n\n"
        f"{action}"
    )
    logger.info("SAVOL %s/%s yuborildi", quiz["index"] + 1, len(quiz["questions"]))
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=kb.mcq_keyboard(q, quiz["arena_id"]),
    )


def _apply_penalty(quiz) -> str:
    """Ketma-ket xatolar uchun achko yechib olish."""
    penalty = ""
    streak = quiz["streak"]
    if streak == 3:
        quiz["score"] = max(0, quiz["score"] - 1)
        penalty = "\n⚠️ Ketma-ket 3 xato: -1 achko"
    elif streak >= 5:
        quiz["score"] = max(0, quiz["score"] - 2)
        penalty = "\n⚠️ Ketma-ket 5 xato: -2 achko"
        quiz["streak"] = 0
    return penalty


async def answer_mcq(update, context: ContextTypes.DEFAULT_TYPE, arena_id, question_id, letter):
    quiz = context.user_data.get("quiz")
    if not quiz or quiz.get("stage") != "mcq":
        restored = db.load_quiz_state(update.effective_user.id)
        if restored and restored.get("stage") == "mcq":
            rq = restored.get("questions", [])
            ri = restored.get("index", 0)
            if ri < len(rq) and str(rq[ri].get("id")) == str(question_id):
                context.user_data["quiz"] = restored
                quiz = restored
            else:
                await safe_edit(update.callback_query, "❌ Bu savol allaqachon javoblangan yoki sessiya yangilangan. /start bosing.")
                return
        else:
            await safe_edit(update.callback_query, "❌ Bu savol allaqachon javoblangan yoki sessiya yangilangan. /start bosing.")
            return

    q = quiz["questions"][quiz["index"]]
    correct = q["correct"]
    points = _question_points(quiz, q)
    if letter == correct:
        quiz["score"] += points
        quiz["streak"] = 0
        feedback = f"✅ To'g'ri! +{points} achko"
    else:
        quiz["streak"] += 1
        penalty = _apply_penalty(quiz)
        feedback = (
            f"❌ Xato. To'g'ri javob: {correct.upper()}) {q[f'opt_{correct}']}"
            f"{penalty}"
        )

    qtype = q.get("question_type")
    if qtype == "idiom":
        feedback += _idiom_detail(q)
        typing_hint = f"2-qism: «{q['en_word']}» idiomasini o'zingiz yozing:"
    elif qtype == "gap":
        typing_hint = f"2-qism: «{q['uz_word']}» gapidagi to'g'ri so'zni yozing:"
    else:
        typing_hint = f"2-qism: «{q['uz_word']}» so'zining inglizchasini o'zingiz yozing:"
    logger.info("1-QISM javobi: %s, jami ball=%s, ketma-ket xato=%s", letter, quiz["score"], quiz["streak"])
    quiz["stage"] = "typing"
    db.save_quiz_state(update.effective_user.id, quiz)
    await safe_edit(update.callback_query, feedback + "\n\n" + typing_hint)


async def handle_typing(update, context: ContextTypes.DEFAULT_TYPE):
    quiz = context.user_data.get("quiz")
    if not quiz or quiz.get("stage") != "typing":
        restored = db.load_quiz_state(update.effective_user.id)
        if restored and restored.get("stage") == "typing":
            context.user_data["quiz"] = restored
            quiz = restored
        else:
            await update.message.reply_text(
                "⚠️ Test sessiyasi topilmadi (bot qayta ishga tushgan bo'lishi mumkin). "
                "Iltimos, /start bosib arenani qaytadan boshlang."
            )
            return

    q = quiz["questions"][quiz["index"]]
    typed = normalize_answer(update.message.text)
    correct_answer = normalize_answer(q["en_word"])
    points = _question_points(quiz, q)

    if typed == correct_answer:
        quiz["score"] += points
        quiz["streak"] = 0
        feedback = f"✅ To'g'ri yozdingiz! +{points} achko"
    else:
        quiz["streak"] += 1
        penalty = _apply_penalty(quiz)
        feedback = f"❌ Xato. To'g'ri yozilishi: {q['en_word']}{penalty}"

    logger.info(
        "2-QISM javobi: %s, jami ball=%s, index=%s/%s",
        typed, quiz["score"], quiz["index"] + 1, len(quiz["questions"]),
    )
    quiz["index"] += 1
    await update.message.reply_text(feedback)

    if quiz["index"] < len(quiz["questions"]):
        quiz["stage"] = "mcq"
        db.save_quiz_state(update.effective_user.id, quiz)
        await send_question(context, update.effective_chat.id)
    else:
        await finish_quiz(update, context)


async def finish_quiz(update, context: ContextTypes.DEFAULT_TYPE):
    quiz = context.user_data.get("quiz") or {}
    score = quiz.get("score", 0)
    max_score = quiz.get("max_score", 1) or 1
    percentage = round(score / max_score * 100, 2)

    if percentage >= MEDAL_GOLD:
        medal = "🥇 OLTIN MEDAL"
    elif percentage >= MEDAL_SILVER:
        medal = "🥈 KUMUSH MEDAL"
    elif percentage >= MEDAL_BRONZE:
        medal = "🥉 BRONZA MEDAL"
    else:
        medal = "🎖 Medal yo'q"

    # Natijani saqlash xatosi xabarni yuborishga to'sqinlik qilmasligi kerak
    try:
        db.save_result(
            quiz.get("user_id"),
            quiz.get("arena_id"),
            score,
            max_score,
            percentage,
            medal,
        )
    except Exception as exc:  # noqa: BLE001 - foydalanuvchiga natija albatta yetib borishi shart
        logger.warning("Natijani saqlab bo'lmadi: %s", exc)

    logger.info("TEST TUGADI: ball=%s/%s foiz=%s medal=%s", score, max_score, percentage, medal)

    context.user_data["quiz"] = None
    context.user_data["flow"] = None
    db.clear_quiz_state(update.effective_user.id)

    text = (
        "🏆 TEST YAKUNLANDI\n\n"
        f"🏟 Arena: {quiz.get('arena_title', '-')}\n"
        f"🎚 Daraja: {quiz.get('level', '-')}\n"
        f"✅ To'plagan achko: {score} / {max_score}\n"
        f"📈 Foiz: {percentage}%\n"
        f"🏅 {medal}\n\n"
        "Yana arenaga kirib, natijangizni yaxshilashingiz mumkin."
    )
    try:
        await update.message.reply_text(text)
    except Exception:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    await show_main(update, context, "🏠 Asosiy menyu:")


async def cancel_arena(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("quiz"):
        if update.message:
            await update.message.reply_text("Siz hech qanday arenada emassiz.")
        else:
            await safe_edit(update.callback_query, "Siz hech qanday arenada emassiz.")
        return
    context.user_data["quiz"] = None
    context.user_data["flow"] = None
    db.clear_quiz_state(update.effective_user.id)
    if update.message:
        await update.message.reply_text(
            "❌ Arenadan chiqdingiz.", reply_markup=kb.back_button("eng_arenas")
        )
    else:
        await safe_edit(update.callback_query, "❌ Arenadan chiqdingiz.", kb.back_button("eng_arenas"))


async def warn_in_arena(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Siz arenadasiz, chiqish uchun /cancel_arena tugmasini bosing."
    )


def _format_percent(value):
    if value is None:
        return "0"
    return f"{float(value):g}"


async def show_my_results(update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user_by_telegram(update.effective_user.id)
    if not user:
        await safe_edit(update.callback_query, "❌ Avval /start bosing.", kb.back_button("eng_arenas"))
        return

    stats = db.get_user_stats(user["id"]) or {}
    results = db.list_user_results(user["id"], limit=10)
    if not results:
        text = "📊 Natijalarim\n\nHali natija yo'q. Arenada test topshiring."
    else:
        lines = [
            "📊 Natijalarim\n",
            f"Urinishlar: {stats.get('attempts', 0)}",
            f"O'rtacha: {_format_percent(stats.get('avg_percent'))}%",
            f"Eng yaxshi: {_format_percent(stats.get('best_percent'))}%",
            f"Jami achko: {stats.get('total_score') or 0}",
            "\nSo'nggi natijalar:",
        ]
        for r in results:
            arena = r.get("arena_title") or "Arena"
            level = r.get("arena_level") or "-"
            lines.append(
                f"• {arena} ({level}) — {r['score']}/{r['max_score']} ({_format_percent(r['percentage'])}%) {r['medal']}"
            )
        text = "\n".join(lines)

    await safe_edit(update.callback_query, text, kb.back_button("eng_arenas"))


async def show_leaderboard(update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.get_leaderboard(limit=10)
    if not rows:
        text = "🏆 Reyting\n\nHali natijalar yo'q."
    else:
        lines = ["🏆 Reyting (top 10)\n"]
        for i, row in enumerate(rows, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lines.append(
                f"{medal} {row['name']} — o'rtacha {_format_percent(row['avg_percent'])}% | "
                f"eng yaxshi {_format_percent(row['best_percent'])}% | urinish {row['attempts']}"
            )
        text = "\n".join(lines)

    await safe_edit(update.callback_query, text, kb.back_button("eng_arenas"))
