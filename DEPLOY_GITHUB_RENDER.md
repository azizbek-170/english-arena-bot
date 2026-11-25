# GitHub + Render + Neon orqali 24/7 ishga tushirish

Bu sxema **karta talab qilmaydi**:

```text
GitHub (kod)
   ↓
Render Free Web Service (bot)
   ↓
Neon Free PostgreSQL (baza)
   ↓
GitHub Actions /health ping (botni uyg'oq tutadi)
```

> Muhendislik nuqtai nazaridan: Render Free web service 15 daqiqa inbound trafik bo'lmasa uxlaydi. Shuning uchun GitHub Actions har 10 daqiqada `/health` ga so'rov yuboradi.

---

## 0. Muhim: faqat bitta bot ishlashi kerak

Render'dagi bot ishga tushganda, kompyuterdagi mahalliy botni to'xtating. Aks holda ikkala bot bir token bilan Telegramga ulanishga urinadi.

Mahalliy botni to'xtatish:

```text
Ctrl + C
```

Agar fon jarayon bo'lsa, keyinroq men to'xtatib beraman.

---

## 1. GitHub repositoriyasi yaratish

1. <https://github.com/new> ga oching.
2. Repository name: `english-arena-bot`.
3. Public yoki Private — ikkalasi ham bo'ladi.
4. **README, .gitignore, license qo'shmang** — hammasi allaqachon bor.
5. **Create repository** bosing.

Keyin PowerShell da:

```powershell
cd "C:\Users\ZETTpro\Documents\Проект по умолчанию\telegram_quiz_bot"
git remote add origin https://github.com/<USERNAME>/english-arena-bot.git
git branch -M main
git push -u origin main
```

`<USERNAME>` o'rniga o'z GitHub username yozing.

> Birinchi pushda GitHub login oynasi chiqishi mumkin. Browser orqali kiring.

---

## 2. Neon Free PostgreSQL yaratish

1. <https://neon.tech> ga oching.
2. GitHub bilan ro'yxatdan o'ting.
3. New Project:
   - Name: `english-arena`
   - Region: sizga yaqini, masalan `eu-central-1`
4. Project ichidan **Connection string** ni nusxalang:

```text
postgresql://user:password@host/dbname?sslmode=require
```

Bu satr keyin Render'da `DATABASE_URL` bo'ladi. **Uni hech kimga yubormang.**

---

## 3. Render Free Web Service yaratish

1. <https://dashboard.render.com> ga oching.
2. GitHub bilan kiring.
3. **New → Web Service**.
4. `english-arena-bot` repositoriyasini tanlang.
5. Sozlamalar:

| Maydon | Qiymat |
|---|---|
| Runtime | Python |
| Plan | Free |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python main.py` |
| Health Check Path | `/health` |

> `render.yaml` fayli bor bo'lgani uchun ko'p sozlamalar o'zi to'ldirilishi mumkin.

6. **Environment Variables** qo'shing:

| Key | Value |
|---|---|
| `BOT_TOKEN` | Hozirgi `.env` dagi BOT_TOKEN |
| `ADMIN_ID` | `8524134316` |
| `DATABASE_URL` | 2-bosqichdagi Neon connection string |

7. **Create Web Service** bosing.
8. Deploy tugagach, Render URL ni nusxalang:

```text
https://english-arena-bot.onrender.com
```

---

## 4. GitHub Actions ping sozlash

1. GitHub repositoriyasiga kiring.
2. **Settings → Secrets and variables → Actions → New repository secret**.
3. Qo'shing:

| Name | Secret |
|---|---|
| `RENDER_URL` | `https://english-arena-bot.onrender.com` |

4. `.github/workflows/keep-alive.yml` allaqachon bor. U har 10 daqiqada:

```text
https://english-arena-bot.onrender.com/health
```

ga so'rov yuboradi va Render Free xizmatini uyg'oq tutadi.

5. Actions bo'limida ishlab turganini tekshiring: `Keep Render bot awake`.

---

## 5. Qo'lda tekshirish

Brauzerda yoki PowerShell da:

```powershell
curl https://english-arena-bot.onrender.com/health
```

Javob:

```text
ok
```

Keyin Telegramda:

```text
/start
```

Bot javob berishi kerak.

---

## 6. Cheklovlar

- Render Free oyiga **750 soat** beradi. Bitta doimiy ishlaydigan servis uchun yetarli.
- Render Free servisni istalgan vaqtda qayta ishga tushirishi mumkin — bot avtomatik qayta ulanadi.
- Neon Free: 1 GB storage, 100 CU-hours/oy — bu bot uchun yetarli.
- GitHub Actions cron biroz kechikishi mumkin. Agar bot ba'zida 1 daqiqa javob bermasa, qo'shimcha ravishda <https://uptimerobot.com> da 5 daqiqali monitoring qo'shing.

---

## 7. Keyingi o'zgartirishlar

Kodni o'zgartirgandan keyin:

```powershell
cd "C:\Users\ZETTpro\Documents\Проект по умолчанию\telegram_quiz_bot"
git add .
git commit -m "Update bot"
git push
```

Render GitHub'ga push bo'lishi bilanoq botni qayta deploy qiladi.
