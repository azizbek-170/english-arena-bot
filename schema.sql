-- Jadvallar bot ishga tushganda avtomatik yaratiladi (database.init_db).
-- Bu fayl qo'lda yaratish uchun qulaylik uchun.

CREATE TABLE IF NOT EXISTS users (
    id           SERIAL PRIMARY KEY,
    telegram_id  BIGINT UNIQUE,
    name         TEXT NOT NULL,
    login        TEXT NOT NULL UNIQUE,
    password     TEXT NOT NULL,
    role         TEXT NOT NULL DEFAULT 'user',
    registered   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS arenas (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    level        TEXT NOT NULL DEFAULT 'A1',
    is_open      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

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
    question_type TEXT NOT NULL DEFAULT 'vocab',  -- vocab | gap | idiom
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Eski bazaga yangi ustunni qo'shish (init_db ham avtomatik bajaradi)
ALTER TABLE questions ADD COLUMN IF NOT EXISTS question_type TEXT NOT NULL DEFAULT 'vocab';

CREATE TABLE IF NOT EXISTS results (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    arena_id     INTEGER REFERENCES arenas(id) ON DELETE SET NULL,
    score        INTEGER NOT NULL,
    max_score    INTEGER NOT NULL,
    percentage   NUMERIC(5,2) NOT NULL,
    medal        TEXT NOT NULL,
    completed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_questions_arena ON questions(arena_id);
CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id);
