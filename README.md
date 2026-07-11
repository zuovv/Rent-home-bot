# Ijara Bot — vositachisiz uy ijarasi elonlari

Uy egalari to'g'ridan-to'g'ri elon joylaydi, ijarachilar filtr orqali qidiradi
(tuman, xona soni, narx, kimlar uchun). Hech qanday rieltor yo'q.

## 1. Bot token olish
1. Telegram'da **@BotFather** ga yozing
2. `/newbot` buyrug'ini yuboring, botga nom va username bering
3. Sizga beriladigan tokenni saqlab qo'ying (masalan: `123456:ABC-DEF...`)

## 2. O'rnatish (kompyuteringizda yoki serverda)
```bash
cd ijara_bot
pip install -r requirements.txt
```

## 3. Tokenni sozlash
Terminalda:
```bash
export BOT_TOKEN="sizning_tokeningiz"
```
Yoki `bot.py` faylidagi shu qatorni to'g'ridan-to'g'ri o'zgartiring:
```python
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
```

## 4. Ishga tushirish
```bash
python bot.py
```
Bot ishga tushgach, Telegram'da botingizga `/start` yozing.

## Buyruqlar va menyu
`/start` yozgach, pastda doimiy menyu chiqadi: **E'lon joylash**, **Uy qidiruv**, **Mening elonlarim**.
Buyruqlar orqali ham ishlaydi:
- `/elon_joylash` — uy egasi uchun: yangi elon joylash (bosqichma-bosqich savol-javob)
- `/qidiruv` — ijarachi uchun: filtr orqali qidirish (tuman → xona soni → kimlar uchun → narx)
- `/mening_elonlarim` — o'z elonlaringizni ko'rish va o'chirish
- `/bekor_qilish` — joriy amalni bekor qilish
- `/tugatish` — rasm yuborishni tugatish (elon joylashda)
- `/otkazish` — ixtiyoriy bosqichni (username, manzil, rasm) o'tkazib yuborish

## Yangi imkoniyatlar
- **Kimlar uchun**: Oila / Talaba Qizlar / Talaba O'g'il bolalar
- **Telegram username** (ixtiyoriy) — telefon raqami yoniga qo'shiladi
- **Manzil**: Telegram location (pin) yoki qo'lda batafsil yozilgan manzil
- **Cheksiz rasm** — bir nechta rasm yuborish mumkin, elon ko'rsatilganda guruh bo'lib chiqadi
- **Avtomatik eskirish** — 20 kundan keyin elon avtomatik nofaol qilinadi (har kuni tekshiriladi)

## Doimiy ishlashi uchun (server kerak)
Bot kompyuteringiz o'chganda to'xtaydi. 24/7 ishlashi uchun arzon VPS kerak
(masalan Beget, Timeweb, yoki Railway.app'ning bepul tarifi). Serverga
`bot.py`, `db.py`, `requirements.txt` fayllarini yuklab, xuddi shu buyruqlarni
bajarish kifoya. Xohlasang, keyingi qadam sifatida shuni ham birga sozlab
beraman.

## Keyingi bosqichlar (tavsiya)
- Elon joylashda uy egasini tasdiqlash (masalan, telefon raqamini SMS orqali
  tekshirish) — fake elonlarni kamaytirish uchun
- 30 kundan keyin elonni avtomatik "eskirgan" deb belgilash
- Reyting/sharh tizimi
- Guruh/kanalga eng yangi elonlarni avtomatik post qilish
