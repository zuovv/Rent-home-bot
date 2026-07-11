"""
Ijara Bot — uy egalari va ijarachilarni vositachisiz bog'lovchi Telegram bot.

Ishga tushirish:
    1. pip install -r requirements.txt
    2. .env faylida BOT_TOKEN ni to'ldiring (yoki quyida BOT_TOKEN o'zgaruvchisiga yozing)
    3. python bot.py
"""
import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
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

TUMANLAR = [
    "Bektemir", "Chilonzor", "Mirzo Ulug'bek", "Mirobod", "Olmazor",
    "Sergeli", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Yashnobod",
    "Yunusobod", "Yangihayot",
]
XONALAR = ["1", "2", "3", "4+"]
KIM_UCHUN = ["Talaba", "Ayollar", "Erkaklar", "Oila", "Barchasi uchun"]

# ---------- Conversation states ----------
(POST_TUMAN, POST_XONA, POST_NARX, POST_KIM, POST_TAVSIF,
 POST_TELEFON, POST_RASM, POST_CONFIRM) = range(8)

(SEARCH_TUMAN, SEARCH_XONA, SEARCH_KIM, SEARCH_NARX) = range(100, 104)


def chunk_buttons(items, prefix, per_row=2, extra_all=True):
    buttons = []
    row = []
    if extra_all:
        items = ["Barchasi"] + items
    for i, item in enumerate(items, 1):
        row.append(InlineKeyboardButton(item, callback_data=f"{prefix}:{item}"))
        if len(row) == per_row:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


# ======================================================================
# START / HELP
# ======================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Assalomu alaykum! 🏠\n\n"
        "Bu bot orqali uy egalari bevosita ijarachilar bilan bog'lanadi — "
        "hech qanday rieltor komissiyasi yo'q.\n\n"
        "/elon_joylash — uyingizni ijaraga qo'yish\n"
        "/qidiruv — mos uy qidirish\n"
        "/mening_elonlarim — o'z elonlaringizni boshqarish\n"
        "/bekor_qilish — joriy amalni bekor qilish"
    )
    await update.message.reply_text(text)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
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
    await q.edit_message_text(f"Tuman: {tuman}\n\nNecha xonali?")
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
        reply_markup=chunk_buttons(KIM_UCHUN, "pkim", per_row=2, extra_all=False),
    )
    return POST_KIM


async def post_kim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kim = q.data.split(":", 1)[1]
    context.user_data["new_listing"]["kim_uchun"] = kim
    await q.edit_message_text(f"Kimlar uchun: {kim}\n\nQisqacha tavsif yozing (sharoiti, manzil, qavat va h.k.):")
    return POST_TAVSIF


async def post_tavsif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["tavsif"] = update.message.text.strip()
    await update.message.reply_text("Bog'lanish uchun telefon raqamingiz? (masalan: +998901234567)")
    return POST_TELEFON


async def post_telefon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["telefon"] = update.message.text.strip()
    await update.message.reply_text(
        "Uyning bitta suratini yuboring (ixtiyoriy). O'tkazib yuborish uchun /otkazish yozing."
    )
    return POST_RASM


async def post_rasm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file_id = update.message.photo[-1].file_id
    context.user_data["new_listing"]["photo_file_id"] = photo_file_id
    return await post_show_confirm(update, context)


async def post_rasm_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_listing"]["photo_file_id"] = None
    return await post_show_confirm(update, context)


async def post_show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data["new_listing"]
    summary = (
        f"📋 Elon ma'lumotlari:\n\n"
        f"📍 Tuman: {d['tuman']}\n"
        f"🚪 Xona soni: {d['xona_soni']}\n"
        f"💵 Narx: ${d['narx']}/oy\n"
        f"👥 Kimlar uchun: {d['kim_uchun']}\n"
        f"📝 Tavsif: {d['tavsif']}\n"
        f"📞 Telefon: {d['telefon']}\n\n"
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
        photo_file_id=d.get("photo_file_id"),
    )
    context.user_data.clear()
    await q.edit_message_text(f"✅ Elon joylandi! (ID: {listing_id})\n\nEndi ijarachilar buni /qidiruv orqali topishadi.")
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
    await q.edit_message_text(
        "Necha xonali kerak?",
    )
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
        reply_markup=chunk_buttons(KIM_UCHUN, "skim", per_row=2),
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
        await context.bot.send_message(chat.id, "😔 Hech narsa topilmadi. Filtrlarni o'zgartirib ko'ring: /qidiruv")
        return ConversationHandler.END

    await context.bot.send_message(chat.id, f"🔎 Topildi: {total} ta elon")
    for r in results:
        caption = (
            f"📍 {r['tuman']} | 🚪 {r['xona_soni']} xonali | 💵 ${r['narx']}/oy\n"
            f"👥 {r['kim_uchun']}\n\n"
            f"📝 {r['tavsif']}\n\n"
            f"📞 Bog'lanish: {r['telefon']}"
        )
        if r.get("photo_file_id"):
            await context.bot.send_photo(chat.id, r["photo_file_id"], caption=caption)
        else:
            await context.bot.send_message(chat.id, caption)

    if offset + 5 < total:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("➡️ Yana ko'rsatish", callback_data=f"more:{offset+5}")
        ]])
        await context.bot.send_message(chat.id, "Ko'proq natija bor:", reply_markup=keyboard)

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
        await update.message.reply_text("Sizda hali elon yo'q. /elon_joylash orqali qo'shishingiz mumkin.")
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
# MAIN
# ======================================================================
def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    post_conv = ConversationHandler(
        entry_points=[CommandHandler("elon_joylash", post_start)],
        states={
            POST_TUMAN: [CallbackQueryHandler(post_tuman, pattern="^ptuman:")],
            POST_XONA: [CallbackQueryHandler(post_xona, pattern="^pxona:")],
            POST_NARX: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_narx)],
            POST_KIM: [CallbackQueryHandler(post_kim, pattern="^pkim:")],
            POST_TAVSIF: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_tavsif)],
            POST_TELEFON: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_telefon)],
            POST_RASM: [
                MessageHandler(filters.PHOTO, post_rasm),
                CommandHandler("otkazish", post_rasm_skip),
            ],
            POST_CONFIRM: [CallbackQueryHandler(post_confirm, pattern="^confirm:")],
        },
        fallbacks=[CommandHandler("bekor_qilish", cancel)],
    )

    search_conv = ConversationHandler(
        entry_points=[CommandHandler("qidiruv", search_start)],
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
    app.add_handler(post_conv)
    app.add_handler(search_conv)
    app.add_handler(CallbackQueryHandler(show_more, pattern="^more:"))
    app.add_handler(CallbackQueryHandler(delete_listing, pattern="^del:"))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
