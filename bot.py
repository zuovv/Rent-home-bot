"""
Ijara Bot — uy egalari va ijarachilarni vositachisiz bog'lovchi Telegram bot.

Ishga tushirish:
    1. pip install -r requirements.txt
    2. BOT_TOKEN environment o'zgaruvchisini o'rnating
    3. python bot.py
"""
import asyncio
import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputMediaPhoto,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@Ijara_Agent")

TUMANLAR = [
    "Bektemir", "Chilonzor", "Mirzo Ulug'bek", "Mirobod", "Olmazor",
    "Sergeli", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Yashnobod",
    "Yunusobod", "Yangihayot",
]
XONALAR = ["1", "2", "3", "4+"]
KIM_UCHUN = ["Oila", "Talaba Qizlar", "Talaba O'g'il bolalar"]

# Doimiy pastki menyu tugmalari
BTN_ELON = "📝 E'lon joylash"
BTN_QIDIRUV = "🔍 Uy qidiruv"
BTN_MENING = "📋 Mening elonlarim"

MAIN_MENU = ReplyKeyboardMarkup(
    [[BTN_ELON], [BTN_QIDIRUV], [BTN_MENING]],
    resize_keyboard=True,
    is_persistent=True,
)

# ---------- Conversation states ----------
(POST_TUMAN, POST_XONA, POST_NARX, POST_KIM, POST_TAVSIF,
 POST_TELEFON, POST_USERNAME, POST_MANZIL, POST_RASM, POST_CONFIRM) = range(10)

(SEARCH_TUMAN, SEARCH_XONA, SEARCH_KIM, SEARCH_NARX) = range(100, 104)


def chunk_buttons(items, prefix, per_row=2, extra_all=True):
    buttons = []
    row = []
    if extra_all:
        items = ["Barchasi"] + items
    for item in items:
        row.append(InlineKeyboardButton(item, callback_data=f"{prefix}:{item}"))
        if len(row) == per_row:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


# ======================================================================
# START / HELP / CANCEL
# ======================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Assalomu alaykum! 🏠\n\n"
        "Bu bot orqali uy egalari bevosita ijarachilar bilan bog'lanadi — "
        "hech qanday rieltor komissiyasi yo'q.\n\n"
        "Pastdagi menyudan kerakli bo'limni tanlang."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Bekor qilindi.", reply_markup=MAIN_MENU)
    return ConversationHandler.END


# ======================================================================
# ELON JOYLASH (owner posting flow)
# ======================================================================
async def post_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"] = {}
    await update.message.reply_text(
        "Qaysi tumanda joylashgan?",
        reply_markup=chunk_buttons(TUMANLAR, "ptuman", per_row=2, extra_all=False),
    )
    return POST_TUMAN


async def post_tuman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    tuman = q.data.split(":", 1)[1]
    context.user_data["new_listing"]["tuman"] = tuman
    await q.edit_message_text(f"Tuman: {tuman}")
    await q.message.reply_text(
        "Xona sonini tanlang:",
        reply_markup=chunk_buttons(XONALAR, "pxona", per_row=4, extra_all=False),
    )
    return POST_XONA


async def post_xona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    xona = q.data.split(":", 1)[1]
    context.user_data["new_listing"]["xona_soni"] = xona
    await q.edit_message_text(f"Xona soni: {xona}\n\nOylik narxi qancha? (faqat raqam, $ da, masalan: 300)")
    return POST_NARX


async def post_narx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "")
    if not text.isdigit():
        await update.message.reply_text("Iltimos, faqat raqam kiriting (masalan: 300).")
        return POST_NARX
    context.user_data["new_listing"]["narx"] = int(text)
    await update.message.reply_text(
        "Kimlar uchun mos?",
        reply_markup=chunk_buttons(KIM_UCHUN, "pkim", per_row=1, extra_all=False),
    )
    return POST_KIM


async def post_kim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kim = q.data.split(":", 1)[1]
    context.user_data["new_listing"]["kim_uchun"] = kim
    await q.edit_message_text(f"Kimlar uchun: {kim}\n\nQisqacha tavsif yozing (sharoiti, qavat va h.k.):")
    return POST_TAVSIF


async def post_tavsif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["tavsif"] = update.message.text.strip()
    await update.message.reply_text("Bog'lanish uchun telefon raqamingiz? (masalan: +998901234567)")
    return POST_TELEFON


async def post_telefon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["telefon"] = update.message.text.strip()
    await update.message.reply_text(
        "Telegram username'ingiz bo'lsa yozing (masalan: @username).\n"
        "Ixtiyoriy — o'tkazib yuborish uchun /otkazish yozing."
    )
    return POST_USERNAME


async def post_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["contact_username"] = update.message.text.strip()
    return await post_ask_manzil(update, context)


async def post_username_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["contact_username"] = None
    return await post_ask_manzil(update, context)


async def post_ask_manzil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Endi uy manzilini yuboring:\n"
        "📍 Telegram orqali joylashuv (location) yuboring,\n"
        "YOKI\n"
        "✍️ Manzilni yozma ravishda batafsil kiriting (ko'cha, mo'ljal va h.k.)"
    )
    return POST_MANZIL


async def post_manzil_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    context.user_data["new_listing"]["latitude"] = loc.latitude
    context.user_data["new_listing"]["longitude"] = loc.longitude
    context.user_data["new_listing"]["manzil_text"] = None
    return await post_ask_rasm(update, context)


async def post_manzil_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["manzil_text"] = update.message.text.strip()
    context.user_data["new_listing"]["latitude"] = None
    context.user_data["new_listing"]["longitude"] = None
    return await post_ask_rasm(update, context)


async def post_ask_rasm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["photos"] = []
    await update.message.reply_text(
        "Endi uyning suratlarini yuboring — xohlagancha rasm yuborishingiz mumkin, "
        "birma-bir yuboring.\n\n"
        "Barcha rasmlarni yuborib bo'lgach, /tugatish deb yozing.\n"
        "Agar rasm qo'shmoqchi bo'lmasangiz, /otkazish deb yozing."
    )
    return POST_RASM


async def post_rasm_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file_id = update.message.photo[-1].file_id
    context.user_data["new_listing"]["photos"].append(photo_file_id)
    count = len(context.user_data["new_listing"]["photos"])
    await update.message.reply_text(f"✅ Rasm qabul qilindi ({count} ta). Yana yuboring yoki /tugatish deb yozing.")
    return POST_RASM


async def post_rasm_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["photos"] = []
    return await post_show_confirm(update, context)


async def post_rasm_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await post_show_confirm(update, context)


async def post_show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data["new_listing"]
    manzil_line = d.get("manzil_text") or ("📍 Joylashuv (location) biriktirilgan" if d.get("latitude") else "—")
    username_line = d.get("contact_username") or "—"
    summary = (
        f"📋 Elon ma'lumotlari:\n\n"
        f"📍 Tuman: {d['tuman']}\n"
        f"🚪 Xona soni: {d['xona_soni']}\n"
        f"💵 Narx: ${d['narx']}/oy\n"
        f"👥 Kimlar uchun: {d['kim_uchun']}\n"
        f"📝 Tavsif: {d['tavsif']}\n"
        f"📞 Telefon: {d['telefon']}\n"
        f"👤 Username: {username_line}\n"
        f"🏠 Manzil: {manzil_line}\n"
        f"🖼 Rasmlar: {len(d.get('photos', []))} ta\n\n"
        f"Joylashtiramizmi?"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ha, joylash", callback_data="confirm:yes")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="confirm:no")],
    ])
    await update.message.reply_text(summary, reply_markup=keyboard)
    return POST_CONFIRM


async def post_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "confirm:no":
        context.user_data.clear()
        await q.edit_message_text("Bekor qilindi.")
        return ConversationHandler.END

    d = context.user_data["new_listing"]
    user = update.effective_user
    listing_id = db.add_listing(
        owner_id=user.id,
        owner_username=user.username or user.first_name,
        tuman=d["tuman"],
        xona_soni=d["xona_soni"],
        narx=d["narx"],
        kim_uchun=d["kim_uchun"],
        tavsif=d["tavsif"],
        telefon=d["telefon"],
        contact_username=d.get("contact_username"),
        manzil_text=d.get("manzil_text"),
        latitude=d.get("latitude"),
        longitude=d.get("longitude"),
        photo_file_ids=d.get("photos", []),
    )
    context.user_data.clear()
    await q.edit_message_text(f"✅ Elon joylandi! (ID: {listing_id})\n\nEndi ijarachilar buni qidiruv orqali topishadi.")

    # Yangi elonni guruhga avtomatik joylash (10 soniyadan ortiq kutmaydi, botni to'xtatib qo'ymaydi)
    try:
        listing = db.get_listing(listing_id)
        await asyncio.wait_for(send_listing_card(context, CHANNEL_USERNAME, listing), timeout=10)
    except asyncio.TimeoutError:
        logger.warning(f"Guruhga yuborish 10 soniyada tugamadi (ID {listing_id}), o'tkazib yuborildi.")
    except Exception:
        logger.warning(f"Elon guruhga yuborilmadi (ID {listing_id})", exc_info=True)

    return ConversationHandler.END


# ======================================================================
# QIDIRUV (search flow)
# ======================================================================
async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["filters"] = {}
    await update.message.reply_text(
        "Qaysi tumanni qidiryapsiz?",
        reply_markup=chunk_buttons(TUMANLAR, "stuman", per_row=2),
    )
    return SEARCH_TUMAN


async def search_tuman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["filters"]["tuman"] = q.data.split(":", 1)[1]
    await q.edit_message_text("Necha xonali kerak?")
    await q.message.reply_text(
        "Xona sonini tanlang:",
        reply_markup=chunk_buttons(XONALAR, "sxona", per_row=4),
    )
    return SEARCH_XONA


async def search_xona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["filters"]["xona_soni"] = q.data.split(":", 1)[1]
    await q.edit_message_text("Kimlar uchun qidiryapsiz?")
    await q.message.reply_text(
        "Tanlang:",
        reply_markup=chunk_buttons(KIM_UCHUN, "skim", per_row=1),
    )
    return SEARCH_KIM


async def search_kim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["filters"]["kim_uchun"] = q.data.split(":", 1)[1]
    await q.edit_message_text(
        "Maksimal narxni kiriting ($ da, masalan: 400).\n"
        "Cheklov qo'ymaslik uchun /otkazish yozing."
    )
    return SEARCH_NARX


async def search_narx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Iltimos, faqat raqam kiriting yoki /otkazish yozing.")
        return SEARCH_NARX
    context.user_data["filters"]["max_narx"] = int(text)
    return await show_results(update, context)


async def search_narx_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["filters"]["max_narx"] = None
    return await show_results(update, context)


async def send_listing_card(context: ContextTypes.DEFAULT_TYPE, chat_id, r):
    username_line = f"\n👤 Telegram: {r['contact_username']}" if r.get("contact_username") else ""
    manzil_line = f"\n🏠 Manzil: {r['manzil_text']}" if r.get("manzil_text") else ""
    caption = (
        f"📍 {r['tuman']} | 🚪 {r['xona_soni']} xonali | 💵 ${r['narx']}/oy\n"
        f"👥 {r['kim_uchun']}\n\n"
        f"📝 {r['tavsif']}"
        f"{manzil_line}\n\n"
        f"📞 Bog'lanish: {r['telefon']}{username_line}"
    )
    photos = r.get("photo_file_ids") or []
    if len(photos) > 1:
        media = [InputMediaPhoto(pid, caption=caption if i == 0 else None) for i, pid in enumerate(photos)]
        await context.bot.send_media_group(chat_id, media)
    elif len(photos) == 1:
        await context.bot.send_photo(chat_id, photos[0], caption=caption)
    else:
        await context.bot.send_message(chat_id, caption)

    if r.get("latitude") and r.get("longitude"):
        await context.bot.send_location(chat_id, r["latitude"], r["longitude"])


async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE, offset=0):
    f = context.user_data.get("filters", {})
    results = db.search_listings(
        tuman=f.get("tuman"), xona_soni=f.get("xona_soni"),
        kim_uchun=f.get("kim_uchun"), max_narx=f.get("max_narx"),
        limit=5, offset=offset,
    )
    total = db.count_listings(
        tuman=f.get("tuman"), xona_soni=f.get("xona_soni"),
        kim_uchun=f.get("kim_uchun"), max_narx=f.get("max_narx"),
    )

    chat = update.effective_chat
    if total == 0:
        await context.bot.send_message(chat.id, "😔 Hech narsa topilmadi. Filtrlarni o'zgartirib ko'ring.", reply_markup=MAIN_MENU)
        return ConversationHandler.END

    await context.bot.send_message(chat.id, f"🔎 Topildi: {total} ta elon")
    for r in results:
        await send_listing_card(context, chat.id, r)

    if offset + 5 < total:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("➡️ Yana ko'rsatish", callback_data=f"more:{offset+5}")
        ]])
        await context.bot.send_message(chat.id, "Ko'proq natija bor:", reply_markup=keyboard)
    else:
        await context.bot.send_message(chat.id, "Qidiruv tugadi.", reply_markup=MAIN_MENU)

    return ConversationHandler.END


async def show_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    offset = int(q.data.split(":", 1)[1])
    await show_results(update, context, offset=offset)


# ======================================================================
# MENING ELONLARIM (manage own listings)
# ======================================================================
async def my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    listings = db.get_user_listings(user.id)
    if not listings:
        await update.message.reply_text("Sizda hali elon yo'q. Pastdagi menyudan 'E'lon joylash' orqali qo'shishingiz mumkin.", reply_markup=MAIN_MENU)
        return
    for r in listings:
        status = "✅ Faol" if r["is_active"] else "❌ O'chirilgan"
        text = (
            f"ID: {r['id']} | {status}\n"
            f"📍 {r['tuman']} | 🚪 {r['xona_soni']} xonali | 💵 ${r['narx']}\n"
            f"👥 {r['kim_uchun']}"
        )
        keyboard = None
        if r["is_active"]:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🗑 O'chirish", callback_data=f"del:{r['id']}")
            ]])
        await update.message.reply_text(text, reply_markup=keyboard)


async def delete_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    listing_id = int(q.data.split(":", 1)[1])
    db.deactivate_listing(listing_id, update.effective_user.id)
    await q.edit_message_text("Elon o'chirildi.")


# ======================================================================
# AVTOMATIK ESKIRGAN ELONLARNI O'CHIRISH
# ======================================================================
async def expire_old_listings_job(context: ContextTypes.DEFAULT_TYPE):
    count = db.deactivate_expired_listings()
    if count:
        logger.info(f"{count} ta eskirgan elon avtomatik o'chirildi.")


async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Handler ichida kutilmagan xato yuz berdi:", exc_info=context.error)


# ======================================================================
# MAIN
# ======================================================================
def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_error_handler(error_handler)

    post_entry = [CommandHandler("elon_joylash", post_start), MessageHandler(filters.Regex(f"^{BTN_ELON}$"), post_start)]
    search_entry = [CommandHandler("qidiruv", search_start), MessageHandler(filters.Regex(f"^{BTN_QIDIRUV}$"), search_start)]

    post_conv = ConversationHandler(
        entry_points=post_entry,
        states={
            POST_TUMAN: [CallbackQueryHandler(post_tuman, pattern="^ptuman:")],
            POST_XONA: [CallbackQueryHandler(post_xona, pattern="^pxona:")],
            POST_NARX: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_narx)],
            POST_KIM: [CallbackQueryHandler(post_kim, pattern="^pkim:")],
            POST_TAVSIF: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_tavsif)],
            POST_TELEFON: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_telefon)],
            POST_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, post_username),
                CommandHandler("otkazish", post_username_skip),
            ],
            POST_MANZIL: [
                MessageHandler(filters.LOCATION, post_manzil_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, post_manzil_text),
            ],
            POST_RASM: [
                MessageHandler(filters.PHOTO, post_rasm_add),
                CommandHandler("tugatish", post_rasm_finish),
                CommandHandler("otkazish", post_rasm_skip),
            ],
            POST_CONFIRM: [CallbackQueryHandler(post_confirm, pattern="^confirm:")],
        },
        fallbacks=[CommandHandler("bekor_qilish", cancel)],
    )

    search_conv = ConversationHandler(
        entry_points=search_entry,
        states={
            SEARCH_TUMAN: [CallbackQueryHandler(search_tuman, pattern="^stuman:")],
            SEARCH_XONA: [CallbackQueryHandler(search_xona, pattern="^sxona:")],
            SEARCH_KIM: [CallbackQueryHandler(search_kim, pattern="^skim:")],
            SEARCH_NARX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_narx),
                CommandHandler("otkazish", search_narx_skip),
            ],
        },
        fallbacks=[CommandHandler("bekor_qilish", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mening_elonlarim", my_listings))
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_MENING}$"), my_listings))
    app.add_handler(post_conv)
    app.add_handler(search_conv)
    app.add_handler(CallbackQueryHandler(show_more, pattern="^more:"))
    app.add_handler(CallbackQueryHandler(delete_listing, pattern="^del:"))

    if app.job_queue:
        app.job_queue.run_repeating(expire_old_listings_job, interval=60 * 60 * 24, first=10)
    else:
        logger.warning("JobQueue mavjud emas — 'pip install python-telegram-bot[job-queue]' qiling.")

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
