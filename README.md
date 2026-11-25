# Telegram Quiz Bot (Ingiliz tili arenasi)

**Texnologiyalar:** Python 3.10+, python-telegram-bot 22.3, PostgreSQL (psycopg 3).

Admin musobaqalar (arenalar) yaratadi, ularga savol qo'shadi yoki AI orqali tayyor lug'at/gap-fill/idiom to'plamini yuklaydi.
Ishtirokchilar ikki bosqichli test topshiradi: variant tanlash (`a/b/c/d`) va javobni o'zi yozish (typing).

24/7 ishga tushirish bo'yicha qo'llanma: [`DEPLOY_GITHUB_RENDER.md`](DEPLOY_GITHUB_RENDER.md) (GitHub + Render Free + Neon Free, karta kerak emas).

**Savol turlari:**
- **Lug'at so'zi** - o'zbekcha so'z/ma'no → inglizcha javob.
- **Definition → Word** - inglizcha ta'rif ko'rsatiladi, to'g'ri so'zni topish/yozish kerak.
- **Gap to'ldirish (gap filling)** - `I ___ from Uzbekistan.` kabi gapdagi nuqta o'rniga to'g'ri so'zni topish.
- **Idiom** - idiom ma'nosini definition bo'yicha topish, keyin idiomni o'zi yozish. Har to'g'ri bosqich **3 achko** beradi (darajadan qat'i nazar).
---

## 1. .env fayli

`.env.example` ni `.env` ga nusxalab, o'zingiznikini yozing:

```env
BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_ID=123456789

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/quiz_bot

DB_HOST=localhost
DB_PORT=5432
DB_NAME=quiz_bot
DB_USER=postgres
DB_PASSWORD=postgres
```

| O'zgaruvchi | Nima uchun | Qayerdan olinadi |
|---|---|---|
| `BOT_TOKEN` | Bot ishlashi uchun | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `ADMIN_ID` | Faqat sizga Admin panel ko'rsatish | [@userinfobot](https://t.me/userinfobot) ga yozing |
| `DATABASE_URL` | PostgreSQL ulanish satri | O'zingiz sozlagan DB ma'lumotlari |
| `DB_HOST` | DB server manzili (DATABASE_URL bo'sh bo'lsa) | `localhost` |
| `DB_PORT` | DB porti | `5432` |
| `DB_NAME` | Baza nomi | `quiz_bot` |
| `DB_USER` | Baza foydalanuvchisi | `postgres` |
| `DB_PASSWORD` | Baza paroli | o'zingizning parolingiz |

> `DATABASE_URL` to'ldirilgan bo'lsa, `DB_*` o'zgaruvchilari e'tiborga olinmaydi.

---

## 2. Terminal komandalari

### PostgreSQL bazasini yaratish

```bash
psql -U postgres -c "CREATE DATABASE quiz_bot;"
```

Yoki pgAdmin orqali `quiz_bot` nomli baza yaratishingiz mumkin.

### Loyihani ishga tushirish

**Windows (PowerShell):**
```powershell
cd telegram_quiz_bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Agar `Activate.ps1` bloklansa:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Linux / macOS:**
```bash
cd telegram_quiz_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

**uv bilan (tavsiya etiladi):**
```powershell
uv venv
uv pip install -r requirements.txt
uv run python main.py
```

Jadvallar bot ishga tushganda **avtomatik** yaratiladi (`init_db()`), shu jumladan eski bazaga `questions.question_type` ustuni ham qo'shib qo'yiladi (migratsiya).
Qo'lda yaratish kerak bo'lsa:

```bash
psql -U postgres -d quiz_bot -f schema.sql
```

---

## 3. Foydalanish tartibi

### Admin
1. `/start` → sizda faqat **Ingiliz tili arenasi** va **Admin panel** tugmalari chiqadi.
2. **Admin panel** → **English arena boshqaruvi** / **Userlar boshqaruvi** / **Statistika**.

**English arena boshqaruvi**
- Arena qo'shish: nomi → tavsif → daraja (A1…C2).
- Arenalar ro'yxati → arena ustiga bosish:
  - arenani ochish/yopish (status),
  - **➕ Savol qo'shish** - avval turini tanlang:
    - *Lug'at so'zi*: o'zbekcha so'z, inglizcha javob, `a/b/c/d` variantlar, to'g'ri harf;
    - *Definition → Word*: inglizcha ta'rif, inglizcha so'z, `a/b/c/d` variantlar, to'g'ri harf;
    - *Gap to'ldirish*: nuqtali gap (masalan `I ___ to school.`), nuqta o'rniga keladigan so'z, `a/b/c/d` variantlar, to'g'ri harf;
    - *Idiom*: idiom, typing uchun idiom o'zi, `a/b/c/d` ma'no (definition) variantlari, to'g'ri harf;
  - **📚 Kitobdan qo'shish** - kitob → unit → savol turi (Vocab / Definition→Word / Gap-fill) tanlab, tayyor savollarni arenaga qo'shish. Hozircha `4000 Essential English Words 1` qo'shilgan: Unit 1 to'liq namunaviy, Unit 2-30 so'z ro'yxati mavjud (ta'rif/misol kiritilgach shu formatda savol generatsiya bo'ladi).
  - **🤖 AI lug'at/gap-fill/idiom** - tanlangan daraja uchun tayyor savollarni yuklaydi;
  - savollar ro'yxati / savol o'chirish,
  - arenani o'chirish.

**Userlar boshqaruvi**
- userlar ro'yxati, tahrirlash, o'chirish.
- Yangi user qo'shish (ism + login + parol) **ixtiyoriy** — ommaviy foydalanuvchilarga login/parol tarqatish shart emas.
- Bunday login/parol faqat eski usulda kirish uchun (`/login` yoki **🔑 Login bilan kirish** tugmasi).

**Statistika**
- Userlar, arenalar, savollar, natijalar soni.
- O'rtacha foiz va eng faol arenalar.

### Ishtirokchi (ommaviy kirish)
1. `/start` bosish kifoya — bot Telegram ID bo'yicha **avtomatik ro'yxatdan o'tkazadi**. Login va parol kerak emas.
2. **Ingiliz tili arenasi** → ochiq arenalar → arenani tanlash.
3. **📊 Natijalarim** — oxirgi 10 ta natija va umumiy statistika.
4. **🏆 Reyting** — top 10 o'quvchi.
5. Savol boshlanadi. Boshqa narsa yozib yuborsangiz:
   `Siz arenadasiz, chiqish uchun /cancel_arena tugmasini bosing.`
6. Chiqish: `/cancel_arena`.

> Admin bergan login/parol bilan kirish kerak bo'lsa: `/login` buyrug'i yoki **🔑 Login bilan kirish** tugmasi. Avtomatik ro'yxatdan o'tish hech kimga xalaqit bermaydi: oldin ro'yxatdan o'tgan userlar o'z hisobi bilan qoladi.

---

## 4. Ball va medallar

Har bir savol (barcha turlar) 2 bosqichdan iborat:

1. **1-qism:** variant tanlash (`a, b, c, d`):
   - lug'at savolida — o'zbekcha so'zning inglizchasini,
   - gap-fill savolida — nuqta o'rniga keladigan so'zni,
   - idiom savolida — idiom ma'nosini (definition).
2. **2-qism:** javobni o'zingiz yozish (typing):
   - lug'at savolida — `«suv» so'zining inglizchasini o'zingiz yozing`,
   - gap-fill savolida — `«I ___ from Uzbekistan.» gapidagi to'g'ri so'zni yozing`,
   - idiom savolida — `«At all costs» idiomasini o'zingiz yozing`.

Har ikki bosqich to'g'ri bajarilsa, achko beriladi:

| Savol turi / Daraja | Achko |
|---|---|
| A1 | 1 |
| A2 | 2 |
| B1 | 3 |
| B2 | 4 |
| C1 / C2 | 5 |
| 💬 Idiom (A1–C2, darajadan qat'i nazar) | **3** |

Idiom savolida to'g'ri javob berilgandan keyin **definition** va **o'zbekcha tarjima** ko'rsatiladi. Daraja faqat idiomlarni saralash/ko'rsatish uchun ishlatiladi.

- Variantlar har safar aralashtiriladi: to'g'ri javob `a/b/c/d` bo'lib navbatlashadi. Shuning uchun faqat `a` ni bosib o'tib bo'lmaydi.
- Xato javob → achko yo'q.
- Ketma-ket **3** xato → **1 achko** yechiladi.
- Ketma-ket **5** xato → yana **2 achko** yechiladi (keyin hisob qaytadan boshlanadi).
- Ball 0 dan pastga tushmaydi.

**Maksimal ball** = barcha savollar bo'yicha `(har bir savolning achkosi × 2)` yig'indisi.

| Foiz | Medal |
|---|---|
| 90–100% | 🥇 Oltin |
| 75–90% | 🥈 Kumush |
| 65–75% | 🥉 Bronza |
| 65% dan past | Medal yo'q |

Natija `results` jadvaliga saqlanadi.

---

## 5. Loyiha tuzilmas

```
telegram_quiz_bot/
├── main.py                 # Kirish nuqtasi, handler marshrutizatsiyasi
├── requirements.txt
├── .env.example
├── schema.sql
├── README.md
└── bot/
    ├── config.py           # .env o'zgaruvchilari, daraja ballari
    ├── database.py         # PostgreSQL bilan ishlash
    ├── keyboards.py        # Reply/Inline tugmalar
    ├── vocabulary.py       # lug'at (60 so'z) + gap-fill (60 gap) + idiom savollari
    ├── idioms_data.py      # 259 ta IELTS idiom: definition + o'zbekcha tarjima + daraja
    ├── utils.py
    ��� books/              # Kitob manbalari (Essential 1 va boshqalar)
    �?   ��� __init__.py     # kitob registri + savol generatsiyasi
    �?   ��� essential1.py   # 4000 Essential English Words 1 (30 unit)
    └── handlers/
        ├── start.py        # /start va ro'yxatdan o'tish
        ├── admin.py        # Admin panel oqimlari
        └── quiz.py         # Test, ball, medal
```
