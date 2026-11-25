"""PostgreSQL bilan ishlash: jadvallar, userlar, arenalar, savollar va natijalar."""

import hashlib
import json
import random
import re
import secrets
from contextlib import closing

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .config import (
    DATABASE_URL,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)
from .utils import normalize_answer

_PBKDF2_ROUNDS = 100_000
_APOSTROPHES = "\u2018\u2019\u02bc\u201a\u2032\u0060\uff07"


def normalize_login(value: str) -> str:
    """Apostrof/bo'shliq/katta-kichik harf farqini tekislaydi."""
    text = (value or "").strip()
    for char in _APOSTROPHES:
        text = text.replace(char, "'")
    text = text.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).lower()


def get_connection():
    if DATABASE_URL:
        return psycopg.connect(DATABASE_URL)
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def _target_db_name() -> str:
    """Ulkanish satridagi baza nomi (yoki DB_NAME)."""
    if DATABASE_URL:
        from urllib.parse import urlsplit

        return urlsplit(DATABASE_URL).path.lstrip("/") or DB_NAME
    return DB_NAME


def _maintenance_connection():
    """Baza yo'q paytda 'postgres' bazasiga ulanish uchun."""
    if DATABASE_URL:
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(DATABASE_URL)
        url = urlunsplit((parts.scheme, parts.netloc, "/postgres", "", ""))
        return psycopg.connect(url, autocommit=True)
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=True,
    )


def ensure_database_exists():
    """Baza hali yaratilmagan bo'lsa, avtomatik yaratadi."""
    try:
        get_connection().close()
        return
    except psycopg.OperationalError as exc:
        if "does not exist" not in str(exc):
            raise
    with closing(_maintenance_connection()) as conn, conn.cursor() as cur:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(_target_db_name())))


def _fetchone(query, params=None):
    with closing(get_connection()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params or ())
            return cur.fetchone()


def _fetchall(query, params=None):
    with closing(get_connection()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params or ())
            return cur.fetchall()


def _execute(query, params=None, returning=False):
    with closing(get_connection()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params or ())
            row = cur.fetchone() if returning else None
        conn.commit()
        return row


# --------------------------------------------------------------------------- #
# Parollarni xavfsiz saqlash (qo'shimcha kutubxonasiz)
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ROUNDS
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _algo, salt, digest = stored.split("$")
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ROUNDS
        ).hex()
        return secrets.compare_digest(candidate, digest)
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# Jadvallarni yaratish
# --------------------------------------------------------------------------- #
def init_db():
    ensure_database_exists()
    with closing(get_connection()) as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id           SERIAL PRIMARY KEY,
                telegram_id  BIGINT UNIQUE,
                name         TEXT NOT NULL,
                login        TEXT NOT NULL UNIQUE,
                password     TEXT NOT NULL,
                role         TEXT NOT NULL DEFAULT 'user',
                registered   BOOLEAN NOT NULL DEFAULT FALSE,
                created_at   TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS arenas (
                id           SERIAL PRIMARY KEY,
                title        TEXT NOT NULL,
                description  TEXT NOT NULL DEFAULT '',
                level        TEXT NOT NULL DEFAULT 'A1',
                is_open      BOOLEAN NOT NULL DEFAULT TRUE,
                created_at   TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id         SERIAL PRIMARY KEY,
                arena_id   INTEGER NOT NULL REFERENCES arenas(id) ON DELETE CASCADE,
                uz_word    TEXT NOT NULL,
                en_word    TEXT NOT NULL,
                opt_a      TEXT NOT NULL,
                opt_b      TEXT NOT NULL,
                opt_c      TEXT NOT NULL,
                opt_d      TEXT NOT NULL,
                correct       TEXT NOT NULL CHECK (correct IN ('a','b','c','d')),
                question_type TEXT NOT NULL DEFAULT 'vocab',
                created_at    TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                id           SERIAL PRIMARY KEY,
                user_id      INTEGER REFERENCES users(id) ON DELETE SET NULL,
                arena_id     INTEGER REFERENCES arenas(id) ON DELETE SET NULL,
                score        INTEGER NOT NULL,
                max_score    INTEGER NOT NULL,
                percentage   NUMERIC(5,2) NOT NULL,
                medal        TEXT NOT NULL,
                completed_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
        # Eski bazaga yangi ustunni qo'shish (migratsiya)
        cur.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'questions' AND column_name = 'question_type'
            """
        )
        if not cur.fetchone():
            cur.execute(
                "ALTER TABLE questions ADD COLUMN question_type TEXT NOT NULL DEFAULT 'vocab'"
            )
        cur.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'quiz_state'
            """
        )
        if not cur.fetchone():
            cur.execute("ALTER TABLE users ADD COLUMN quiz_state TEXT")
        for col, ddl in [
            ("attempt_count", "ALTER TABLE questions ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0"),
            ("wrong_count", "ALTER TABLE questions ADD COLUMN wrong_count INTEGER NOT NULL DEFAULT 0"),
        ]:
            cur.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'questions' AND column_name = %s
                """,
                (col,),
            )
            if not cur.fetchone():
                cur.execute(ddl)
        conn.commit()


# --------------------------------------------------------------------------- #
# Userlar
# --------------------------------------------------------------------------- #
def get_user_by_telegram(telegram_id: int):
    return _fetchone("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))


def get_user_by_id(user_id: int):
    return _fetchone("SELECT * FROM users WHERE id = %s", (user_id,))


def save_quiz_state(telegram_id: int, quiz_state):
    payload = json.dumps(quiz_state, ensure_ascii=False, default=str) if quiz_state is not None else None
    _execute("UPDATE users SET quiz_state = %s WHERE telegram_id = %s", (payload, telegram_id))


def load_quiz_state(telegram_id: int):
    row = _fetchone("SELECT quiz_state FROM users WHERE telegram_id = %s", (telegram_id,))
    if not row or not row.get("quiz_state"):
        return None
    try:
        return json.loads(row["quiz_state"])
    except Exception:
        return None


def clear_quiz_state(telegram_id: int):
    _execute("UPDATE users SET quiz_state = NULL WHERE telegram_id = %s", (telegram_id,))


def get_user_by_login(login: str):
    target = normalize_login(login)
    for user in _fetchall("SELECT * FROM users"):
        if normalize_login(user["login"]) == target:
            return user
    return None


def list_users():
    return _fetchall("SELECT * FROM users ORDER BY id")


def ensure_admin(telegram_id: int, name: str):
    """Admin birinchi /start bosganda uni bazaga kiritadi yoki rolini tasdiqlaydi."""
    existing = get_user_by_telegram(telegram_id)
    if existing:
        return _execute(
            "UPDATE users SET role = 'admin', registered = TRUE WHERE id = %s RETURNING *",
            (existing["id"],),
            returning=True,
        )
    login = f"admin_{telegram_id}"
    if get_user_by_login(login):
        login = f"admin_{telegram_id}_{secrets.token_hex(3)}"
    return _execute(
        """
        INSERT INTO users (telegram_id, name, login, password, role, registered)
        VALUES (%s, %s, %s, %s, 'admin', TRUE)
        RETURNING *
        """,
        (telegram_id, name or "Admin", login, hash_password(secrets.token_urlsafe(16))),
        returning=True,
    )


def ensure_public_user(telegram_id: int, name: str):
    """Ommaviy foydalanuvchini /start bosishi bilanoq ro'yxatdan o'tkazadi."""
    existing = get_user_by_telegram(telegram_id)
    if existing:
        if existing["registered"]:
            return existing
        return _execute(
            "UPDATE users SET registered = TRUE WHERE id = %s RETURNING *",
            (existing["id"],),
            returning=True,
        )
    login = f"tg_{telegram_id}"
    if get_user_by_login(login):
        login = f"tg_{telegram_id}_{secrets.token_hex(3)}"
    return _execute(
        """
        INSERT INTO users (telegram_id, name, login, password, role, registered)
        VALUES (%s, %s, %s, %s, 'user', TRUE)
        RETURNING *
        """,
        (telegram_id, name or "Foydalanuvchi", login, hash_password(secrets.token_urlsafe(16))),
        returning=True,
    )


def create_user(name: str, login: str, password: str):
    return _execute(
        """
        INSERT INTO users (name, login, password, role, registered)
        VALUES (%s, %s, %s, 'user', FALSE)
        RETURNING *
        """,
        (name, login, hash_password(password)),
        returning=True,
    )


def register_user(user_id: int, telegram_id: int):
    return _execute(
        "UPDATE users SET telegram_id = %s, registered = TRUE WHERE id = %s RETURNING *",
        (telegram_id, user_id),
        returning=True,
    )


def update_user(user_id: int, **fields):
    allowed = {"name", "login", "password", "role"}
    sets, values = [], []
    for key, value in fields.items():
        if key in allowed:
            if key == "password":
                value = hash_password(value)
            sets.append(f"{key} = %s")
            values.append(value)
    if not sets:
        return get_user_by_id(user_id)
    values.append(user_id)
    return _execute(
        f"UPDATE users SET {', '.join(sets)} WHERE id = %s RETURNING *",
        tuple(values),
        returning=True,
    )


def delete_user(user_id: int):
    _execute("DELETE FROM users WHERE id = %s", (user_id,))


# --------------------------------------------------------------------------- #
# Arenalar
# --------------------------------------------------------------------------- #
def list_arenas():
    return _fetchall("SELECT * FROM arenas ORDER BY id")


def list_open_arenas():
    return _fetchall("SELECT * FROM arenas WHERE is_open = TRUE ORDER BY id")


def get_arena(arena_id: int):
    return _fetchone("SELECT * FROM arenas WHERE id = %s", (arena_id,))


def create_arena(title: str, description: str, level: str):
    return _execute(
        "INSERT INTO arenas (title, description, level) VALUES (%s, %s, %s) RETURNING *",
        (title, description, level),
        returning=True,
    )


def toggle_arena(arena_id: int):
    return _execute(
        "UPDATE arenas SET is_open = NOT is_open WHERE id = %s RETURNING *",
        (arena_id,),
        returning=True,
    )


def delete_arena(arena_id: int):
    _execute("DELETE FROM arenas WHERE id = %s", (arena_id,))


# --------------------------------------------------------------------------- #
# Savollar
# --------------------------------------------------------------------------- #
def list_questions(arena_id: int):
    return _fetchall("SELECT * FROM questions WHERE arena_id = %s ORDER BY id", (arena_id,))


def get_question(question_id: int):
    return _fetchone("SELECT * FROM questions WHERE id = %s", (question_id,))


def add_question(arena_id, uz, en, a, b, c, d, correct, qtype="vocab"):
    return _execute(
        """
        INSERT INTO questions
            (arena_id, uz_word, en_word, opt_a, opt_b, opt_c, opt_d, correct, question_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (arena_id, uz, en, a, b, c, d, correct, qtype),
        returning=True,
    )


def update_question(question_id: int, **fields):
    allowed = {"uz_word", "en_word", "opt_a", "opt_b", "opt_c", "opt_d", "correct", "question_type"}
    sets = []
    params = []
    for key, value in fields.items():
        if key in allowed and value is not None:
            sets.append(f"{key} = %s")
            params.append(value)
    if not sets:
        return get_question(question_id)
    params.append(question_id)
    return _execute(
        f"UPDATE questions SET {', '.join(sets)} WHERE id = %s RETURNING *",
        tuple(params),
        returning=True,
    )


def record_question_attempt(question_id: int, is_correct: bool):
    if is_correct:
        _execute("UPDATE questions SET attempt_count = attempt_count + 1 WHERE id = %s", (question_id,))
    else:
        _execute(
            "UPDATE questions SET attempt_count = attempt_count + 1, wrong_count = wrong_count + 1 WHERE id = %s",
            (question_id,),
        )


def get_hardest_questions(limit=5):
    return _fetchall(
        """
        SELECT q.id, q.uz_word, q.en_word, q.question_type, q.attempt_count, q.wrong_count,
               a.title AS arena_title,
               CASE WHEN q.attempt_count > 0
                    THEN ROUND((q.wrong_count::numeric * 100 / q.attempt_count), 1)
                    ELSE 0 END AS wrong_percent
        FROM questions q
        LEFT JOIN arenas a ON a.id = q.arena_id
        WHERE q.attempt_count >= 3
        ORDER BY wrong_percent DESC, q.wrong_count DESC, q.attempt_count DESC
        LIMIT %s
        """,
        (limit,),
    )


def delete_question(question_id: int):
    _execute("DELETE FROM questions WHERE id = %s", (question_id,))


def _shuffle_options(correct_text: str, options, force_letter: str = None):
    """Variantlarni aralashtirib, to'g'ri javob harfi bilan qaytaradi."""
    opts = list(options)
    if not opts:
        return opts, "a"
    target = normalize_answer(correct_text)
    idx = next((i for i, o in enumerate(opts) if normalize_answer(o) == target), None)
    correct_option = opts[idx] if idx is not None else opts[0]
    rest = [o for i, o in enumerate(opts) if i != idx] if idx is not None else opts[1:]
    random.shuffle(rest)
    pos = "abcd".index(force_letter) if force_letter in "abcd" else random.randrange(4)
    pos = min(pos, len(rest))
    return rest[:pos] + [correct_option] + rest[pos:], "abcd"[pos]


def shuffle_question_options(question_id: int, force_letter: str = None):
    """Bitta savolning variantlarini aralashtirib saqlaydi."""
    q = get_question(question_id)
    if not q:
        return None
    correct_text = q[f"opt_{q['correct']}"]
    opts, correct = _shuffle_options(
        correct_text, [q[f"opt_{l}"] for l in "abcd"], force_letter
    )
    return _execute(
        """
        UPDATE questions
        SET opt_a = %s, opt_b = %s, opt_c = %s, opt_d = %s, correct = %s
        WHERE id = %s
        RETURNING *
        """,
        (*opts, correct, question_id),
        returning=True,
    )


def shuffle_all_question_options():
    """Barcha mavjud savollarning variantlarini bir marta aralashtiradi."""
    count = 0
    with closing(get_connection()) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM questions")
        for q in cur.fetchall():
            correct_text = q[f"opt_{q['correct']}"]
            opts, correct = _shuffle_options(
                correct_text,
                [q[f"opt_{l}"] for l in "abcd"],
                "abcd"[q["id"] % 4],
            )
            cur.execute(
                """
                UPDATE questions
                SET opt_a = %s, opt_b = %s, opt_c = %s, opt_d = %s, correct = %s
                WHERE id = %s
                """,
                (*opts, correct, q["id"]),
            )
            count += 1
        conn.commit()
    return count


def add_questions_bulk(arena_id: int, items, qtype="vocab"):
    """AI lug'atidan kelgan savollarni qo'shadi (dublikat savollarni o'tkazib yuboradi)."""
    added = 0
    with closing(get_connection()) as conn, conn.cursor() as cur:
        for index, item in enumerate(items):
            cur.execute(
                "SELECT 1 FROM questions WHERE arena_id = %s AND uz_word = %s AND question_type = %s",
                (arena_id, item["uz"], qtype),
            )
            if cur.fetchone():
                continue
            # a/b/c/d navbatlashib keladi -> o'quvchi faqat "a" ni bosolmaydi
            opts, correct = _shuffle_options(
                item["en"], item["options"], "abcd"[index % 4]
            )
            cur.execute(
                """
                INSERT INTO questions
                    (arena_id, uz_word, en_word, opt_a, opt_b, opt_c, opt_d, correct, question_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (arena_id, item["uz"], item["en"], *opts, correct, qtype),
            )
            added += 1
        conn.commit()
    return added


# --------------------------------------------------------------------------- #
# Natijalar
# --------------------------------------------------------------------------- #
def save_result(user_id, arena_id, score, max_score, percentage, medal):
    return _execute(
        """
        INSERT INTO results (user_id, arena_id, score, max_score, percentage, medal)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (user_id, arena_id, score, max_score, percentage, medal),
        returning=True,
    )


def list_user_results(user_id, limit=10):
    return _fetchall(
        """
        SELECT r.*, a.title AS arena_title, a.level AS arena_level
        FROM results r LEFT JOIN arenas a ON a.id = r.arena_id
        WHERE r.user_id = %s ORDER BY r.completed_at DESC LIMIT %s
        """,
        (user_id, limit),
    )


def get_leaderboard(limit=10):
    return _fetchall(
        """
        SELECT
            u.name,
            COUNT(r.id) AS attempts,
            ROUND(AVG(r.percentage)::numeric, 1) AS avg_percent,
            MAX(r.percentage) AS best_percent,
            SUM(r.score) AS total_score
        FROM results r
        JOIN users u ON u.id = r.user_id
        GROUP BY u.id, u.name
        ORDER BY avg_percent DESC, best_percent DESC, total_score DESC
        LIMIT %s
        """,
        (limit,),
    )


def get_user_stats(user_id):
    return _fetchone(
        """
        SELECT
            COUNT(*) AS attempts,
            ROUND(AVG(percentage)::numeric, 1) AS avg_percent,
            MAX(percentage) AS best_percent,
            SUM(score) AS total_score
        FROM results
        WHERE user_id = %s
        """,
        (user_id,),
    )


def list_all_results(limit=5000):
    return _fetchall(
        """
        SELECT r.*, u.name AS user_name, u.login AS user_login, a.title AS arena_title, a.level AS arena_level
        FROM results r
        LEFT JOIN users u ON u.id = r.user_id
        LEFT JOIN arenas a ON a.id = r.arena_id
        ORDER BY r.completed_at DESC
        LIMIT %s
        """,
        (limit,),
    )


def get_admin_stats():
    stats = _fetchone(
        """
        SELECT
            (SELECT COUNT(*) FROM users) AS users_count,
            (SELECT COUNT(*) FROM users WHERE registered = TRUE) AS registered_count,
            (SELECT COUNT(*) FROM arenas) AS arenas_count,
            (SELECT COUNT(*) FROM arenas WHERE is_open = TRUE) AS open_arenas_count,
            (SELECT COUNT(*) FROM questions) AS questions_count,
            (SELECT COUNT(*) FROM results) AS results_count,
            (SELECT ROUND(AVG(percentage)::numeric, 1) FROM results) AS avg_percent
        """
    ) or {}
    top_arenas = _fetchall(
        """
        SELECT a.title, a.level, COUNT(r.id) AS attempts,
               ROUND(AVG(r.percentage)::numeric, 1) AS avg_percent
        FROM results r
        JOIN arenas a ON a.id = r.arena_id
        GROUP BY a.id, a.title, a.level
        ORDER BY attempts DESC, avg_percent DESC
        LIMIT 5
        """
    )
    stats["top_arenas"] = top_arenas
    stats["hardest_questions"] = get_hardest_questions(5)
    return stats
