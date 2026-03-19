"""
ProClean Market — Telegram Bot
Qarshi shahri uchun tozalash xizmatlari marketplace

Ishlatish:
  pip install python-telegram-bot
  python bot.py
"""

import logging
import json
import os
from datetime import datetime
from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

# ─────────────────────────────────────────────
# SOZLAMALAR
# ─────────────────────────────────────────────
BOT_TOKEN = "8661210187:AAG-6g0KNXzAMaVrWIESf3kFEqTRkTxU"   # @BotFather dan olingan token
ADMIN_ID   = 6304522932                          # Sizning Telegram ID raqamingiz

# Ma'lumotlar fayli (haqiqiy DB o'rniga)
DATA_FILE = "data.json"

# ─────────────────────────────────────────────
# CONVERSATION HOLATLARI
# ─────────────────────────────────────────────
(
    # Mijoz uchun
    MIJOZ_XIZMAT,
    MIJOZ_XONA,
    MIJOZ_MANZIL,
    MIJOZ_TELEFON,
    MIJOZ_VAQT,
    MIJOZ_TASDIQLASH,

    # Ijrochi uchun
    IJROCHI_ISM,
    IJROCHI_TELEFON,
    IJROCHI_HUDUD,
    IJROCHI_TASDIQLASH,
) = range(10)

# ─────────────────────────────────────────────
# XIZMAT TURLARI VA NARXLAR
# ─────────────────────────────────────────────
XIZMATLAR = {
    "🏠 Uy tozalash": {
        "tavsif": "1 xona — 50,000 so'm",
        "narx_xona": 50000,
    },
    "🏢 Ofis tozalash": {
        "tavsif": "1 ish joyi — 30,000 so'm",
        "narx_xona": 30000,
    },
    "🛋️ Divan/gilam yuvish": {
        "tavsif": "1 dona — 80,000 so'm",
        "narx_xona": 80000,
    },
    "🪟 Oyna yuvish": {
        "tavsif": "1 qavatli — 40,000 so'm",
        "narx_xona": 40000,
    },
    "🏗️ Remontdan keyingi": {
        "tavsif": "1 xona — 100,000 so'm",
        "narx_xona": 100000,
    },
    "✨ Boshqa": {
        "tavsif": "Narx kelishiladi",
        "narx_xona": 0,
    },
}

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# MA'LUMOTLAR BAZASI (JSON fayl)
# ─────────────────────────────────────────────
def db_load():
    """JSON fayldan ma'lumotlarni yuklash"""
    if not os.path.exists(DATA_FILE):
        return {"buyurtmalar": [], "ijrochilar": [], "counter": 0}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def db_save(data):
    """Ma'lumotlarni JSON faylga saqlash"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def yangi_buyurtma_id():
    data = db_load()
    data["counter"] += 1
    db_save(data)
    return data["counter"]


# ─────────────────────────────────────────────
# /start — BOSHLASH
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        ["📋 Buyurtma berish"],
        ["👷 Ijrochi bo'lish"],
        ["ℹ️ Platforma haqida"],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "🧹 *ProClean Market*ga xush kelibsiz!\n"
        "Qarshi shahridagi professional tozalash xizmatlari platformasi.\n\n"
        "Nima qilmoqchisiz?",
        parse_mode="Markdown",
        reply_markup=markup,
    )


# ─────────────────────────────────────────────
# BUYURTMA BERISH — MIJOZ OQIMI
# ─────────────────────────────────────────────
async def buyurtma_boshlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    xizmat_list = list(XIZMATLAR.keys())
    keyboard = [[x] for x in xizmat_list]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "🧹 *Xizmat turini tanlang:*",
        parse_mode="Markdown",
        reply_markup=markup,
    )
    return MIJOZ_XIZMAT


async def mijoz_xizmat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    xizmat = update.message.text
    if xizmat not in XIZMATLAR:
        await update.message.reply_text("Iltimos, ro'yxatdan tanlang.")
        return MIJOZ_XIZMAT

    context.user_data["xizmat"] = xizmat
    info = XIZMATLAR[xizmat]

    keyboard = [["1", "2", "3"], ["4", "5", "6+"], ["⬅️ Orqaga"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"✅ Tanladingiz: *{xizmat}*\n"
        f"💰 Narx: {info['tavsif']}\n\n"
        "Nechta xona/dona?",
        parse_mode="Markdown",
        reply_markup=markup,
    )
    return MIJOZ_XONA


async def mijoz_xona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matn = update.message.text
    if matn == "⬅️ Orqaga":
        return await buyurtma_boshlash(update, context)

    try:
        xona = int(matn.replace("6+", "6"))
    except ValueError:
        await update.message.reply_text("Raqam kiriting (1-6).")
        return MIJOZ_XONA

    context.user_data["xona"] = xona
    xizmat = context.user_data["xizmat"]
    narx = XIZMATLAR[xizmat]["narx_xona"] * xona

    context.user_data["narx"] = narx

    await update.message.reply_text(
        f"📍 *Manzilingizni yozing*\n"
        f"(Ko'cha nomi, uy raqami)\n\n"
        f"Masalan: _Navoiy ko'chasi, 15-uy_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return MIJOZ_MANZIL


async def mijoz_manzil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["manzil"] = update.message.text

    await update.message.reply_text(
        "📞 *Telefon raqamingizni yozing:*\n"
        "Masalan: _+998 90 123-45-67_",
        parse_mode="Markdown",
    )
    return MIJOZ_TELEFON


async def mijoz_telefon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefon"] = update.message.text

    keyboard = [
        ["🕐 Imkon qadar tez"],
        ["📅 Bugun kechqurun"],
        ["📅 Ertaga ertalab"],
        ["📅 Vaqtni o'zim belgilayman"],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "⏰ *Qachon kerak?*",
        parse_mode="Markdown",
        reply_markup=markup,
    )
    return MIJOZ_VAQT


async def mijoz_vaqt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["vaqt"] = update.message.text

    d = context.user_data
    xizmat = d["xizmat"]
    narx = d.get("narx", 0)
    narx_matn = f"{narx:,} so'm" if narx > 0 else "Kelishiladi"

    keyboard = [["✅ Tasdiqlash", "❌ Bekor qilish"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"📋 *Buyurtmangizni tekshiring:*\n\n"
        f"🧹 Xizmat: {xizmat}\n"
        f"🔢 Miqdor: {d['xona']} ta\n"
        f"💰 Taxminiy narx: {narx_matn}\n"
        f"📍 Manzil: {d['manzil']}\n"
        f"📞 Telefon: {d['telefon']}\n"
        f"⏰ Vaqt: {d['vaqt']}\n\n"
        f"Tasdiqlaysizmi?",
        parse_mode="Markdown",
        reply_markup=markup,
    )
    return MIJOZ_TASDIQLASH


async def mijoz_tasdiqlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        await update.message.reply_text(
            "Buyurtma bekor qilindi.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    # Buyurtmani saqlash
    d = context.user_data
    buyurtma_id = yangi_buyurtma_id()
    narx = d.get("narx", 0)
    narx_matn = f"{narx:,} so'm" if narx > 0 else "Kelishiladi"

    buyurtma = {
        "id": buyurtma_id,
        "mijoz_id": update.effective_user.id,
        "mijoz_ism": update.effective_user.full_name,
        "xizmat": d["xizmat"],
        "xona": d["xona"],
        "narx": narx,
        "manzil": d["manzil"],
        "telefon": d["telefon"],
        "vaqt": d["vaqt"],
        "holat": "yangi",
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }

    data = db_load()
    data["buyurtmalar"].append(buyurtma)
    db_save(data)

    # Mijozga tasdiqlash
    keyboard = [["📋 Buyurtma berish"], ["👷 Ijrochi bo'lish"], ["ℹ️ Platforma haqida"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ *Buyurtma #{buyurtma_id} qabul qilindi!*\n\n"
        f"Tez orada ijrochi siz bilan bog'lanadi.\n"
        f"📞 Telefon: {d['telefon']}",
        parse_mode="Markdown",
        reply_markup=markup,
    )

    # Adminga va ijrochilarga xabar yuborish
    xabar = (
        f"🆕 *Yangi buyurtma #{buyurtma_id}*\n\n"
        f"🧹 {d['xizmat']} — {d['xona']} ta\n"
        f"💰 {narx_matn}\n"
        f"📍 {d['manzil']}\n"
        f"📞 {d['telefon']}\n"
        f"⏰ {d['vaqt']}\n"
        f"👤 {update.effective_user.full_name}"
    )

    # Adminга yuborish
    try:
        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Qabul qilish (#{buyurtma_id})",
                                  callback_data=f"qabul_{buyurtma_id}")]
        ])
        await context.bot.send_message(
            chat_id=ADMIN_ID, text=xabar,
            parse_mode="Markdown", reply_markup=inline_kb
        )
    except Exception as e:
        logger.warning(f"Adminga yuborishda xato: {e}")

    # Ro'yxatdagi ijrochilarga yuborish
    await ijrochilarga_yuborish(context, xabar, buyurtma_id)

    context.user_data.clear()
    return ConversationHandler.END


async def ijrochilarga_yuborish(context, xabar, buyurtma_id):
    """Barcha ijrochilarga buyurtma haqida xabar yuborish"""
    data = db_load()
    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Men olaman (#{buyurtma_id})",
                              callback_data=f"qabul_{buyurtma_id}")]
    ])
    for ijrochi in data.get("ijrochilar", []):
        if ijrochi.get("holat") == "faol":
            try:
                await context.bot.send_message(
                    chat_id=ijrochi["telegram_id"],
                    text=xabar,
                    parse_mode="Markdown",
                    reply_markup=inline_kb,
                )
            except Exception as e:
                logger.warning(f"Ijrochiga yuborishda xato {ijrochi['telegram_id']}: {e}")


# ─────────────────────────────────────────────
# IJROCHI ROYXATDAN OTISH
# ─────────────────────────────────────────────
async def ijrochi_royxat_boshlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👷 *Ijrochi sifatida ro'yxatdan o'tish*\n\n"
        "To'liq ismingizni yozing:\n"
        "_Masalan: Karimov Jasur_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return IJROCHI_ISM


async def ijrochi_ism(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ijrochi_ism"] = update.message.text
    await update.message.reply_text(
        "📞 Telefon raqamingiz:\n_+998 90 ..._",
        parse_mode="Markdown",
    )
    return IJROCHI_TELEFON


async def ijrochi_telefon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ijrochi_telefon"] = update.message.text

    keyboard = [
        ["🏙️ Qarshi markazi"],
        ["🏘️ Yangi hayot"],
        ["🏘️ Ko'kcha"],
        ["🏘️ Barcha hudud"],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "📍 Qaysi hududda ishlaysiz?",
        reply_markup=markup,
    )
    return IJROCHI_HUDUD


async def ijrochi_hudud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ijrochi_hudud"] = update.message.text

    d = context.user_data
    keyboard = [["✅ Tasdiqlash", "❌ Bekor qilish"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"📋 *Ma'lumotlaringiz:*\n\n"
        f"👤 Ism: {d['ijrochi_ism']}\n"
        f"📞 Telefon: {d['ijrochi_telefon']}\n"
        f"📍 Hudud: {d['ijrochi_hudud']}\n\n"
        f"Tasdiqlaysizmi?",
        parse_mode="Markdown",
        reply_markup=markup,
    )
    return IJROCHI_TASDIQLASH


async def ijrochi_tasdiqlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        await update.message.reply_text("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    d = context.user_data
    ijrochi = {
        "telegram_id": update.effective_user.id,
        "ism": d["ijrochi_ism"],
        "telefon": d["ijrochi_telefon"],
        "hudud": d["ijrochi_hudud"],
        "holat": "kutmoqda",   # admin tasdiqlagunicha
        "reyting": 0.0,
        "buyurtmalar": 0,
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }

    data = db_load()
    # Takroriy ro'yxatdan o'tishni tekshirish
    mavjud = any(i["telegram_id"] == ijrochi["telegram_id"] for i in data["ijrochilar"])
    if not mavjud:
        data["ijrochilar"].append(ijrochi)
        db_save(data)

    keyboard = [["📋 Buyurtma berish"], ["👷 Ijrochi bo'lish"], ["ℹ️ Platforma haqida"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "✅ *Arizangiz qabul qilindi!*\n\n"
        "Admin tekshirib, tez orada faollashtiradi.\n"
        "Faollashtirilganda xabar olasiz. 🙌",
        parse_mode="Markdown",
        reply_markup=markup,
    )

    # Adminга xabar
    try:
        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"✅ Faollashtirish — {d['ijrochi_ism']}",
                callback_data=f"faol_{update.effective_user.id}"
            )]
        ])
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👷 *Yangi ijrochi arizasi*\n\n"
                 f"👤 {d['ijrochi_ism']}\n"
                 f"📞 {d['ijrochi_telefon']}\n"
                 f"📍 {d['ijrochi_hudud']}\n"
                 f"🆔 ID: {update.effective_user.id}",
            parse_mode="Markdown",
            reply_markup=inline_kb,
        )
    except Exception as e:
        logger.warning(f"Admin xabari xato: {e}")

    context.user_data.clear()
    return ConversationHandler.END


# ─────────────────────────────────────────────
# CALLBACK QUERY — TUGMALAR
# ─────────────────────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_str = query.data

    # Buyurtmani qabul qilish
    if data_str.startswith("qabul_"):
        buyurtma_id = int(data_str.split("_")[1])
        data = db_load()

        buyurtma = next((b for b in data["buyurtmalar"] if b["id"] == buyurtma_id), None)
        if not buyurtma:
            await query.edit_message_text("Bu buyurtma topilmadi.")
            return

        if buyurtma["holat"] != "yangi":
            await query.edit_message_text(
                f"Bu buyurtma allaqachon qabul qilingan."
            )
            return

        buyurtma["holat"] = "qabul_qilindi"
        buyurtma["ijrochi_id"] = query.from_user.id
        buyurtma["ijrochi_ism"] = query.from_user.full_name
        db_save(data)

        await query.edit_message_text(
            f"✅ Buyurtma #{buyurtma_id} siz tomondan qabul qilindi!\n"
            f"📞 Mijoz: {buyurtma['telefon']}\n"
            f"📍 Manzil: {buyurtma['manzil']}"
        )

        # Mijozga xabar yuborish
        try:
            await context.bot.send_message(
                chat_id=buyurtma["mijoz_id"],
                text=f"🎉 *Buyurtma #{buyurtma_id} qabul qilindi!*\n\n"
                     f"👷 Ijrochi: {query.from_user.full_name}\n"
                     f"Tez orada siz bilan bog'lanadi.",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(f"Mijozga xabar xato: {e}")

    # Ijrochini faollashtirish (admin)
    elif data_str.startswith("faol_"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("Siz admin emassiz!", show_alert=True)
            return

        ijrochi_telegram_id = int(data_str.split("_")[1])
        data = db_load()

        for ijrochi in data["ijrochilar"]:
            if ijrochi["telegram_id"] == ijrochi_telegram_id:
                ijrochi["holat"] = "faol"
                break
        db_save(data)

        await query.edit_message_text(
            f"✅ Ijrochi faollashtirildi: ID {ijrochi_telegram_id}"
        )

        try:
            await context.bot.send_message(
                chat_id=ijrochi_telegram_id,
                text="🎉 *Tabriklaymiz!*\n\n"
                     "Sizning ProClean Market da profilingiz faollashtirildi.\n"
                     "Endi yangi buyurtmalar haqida xabar olasiz! 💪",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(f"Ijrochiga xabar xato: {e}")


# ─────────────────────────────────────────────
# ADMIN PANEL — /admin
# ─────────────────────────────────────────────
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bu buyruq faqat admin uchun.")
        return

    data = db_load()
    buyurtmalar = data.get("buyurtmalar", [])
    ijrochilar = data.get("ijrochilar", [])

    yangi = sum(1 for b in buyurtmalar if b["holat"] == "yangi")
    qabul = sum(1 for b in buyurtmalar if b["holat"] == "qabul_qilindi")
    faol_ijrochilar = sum(1 for i in ijrochilar if i["holat"] == "faol")
    kutmoqda = sum(1 for i in ijrochilar if i["holat"] == "kutmoqda")

    await update.message.reply_text(
        f"📊 *Admin panel*\n\n"
        f"📋 Buyurtmalar:\n"
        f"  🆕 Yangi: {yangi}\n"
        f"  ✅ Qabul qilingan: {qabul}\n"
        f"  📦 Jami: {len(buyurtmalar)}\n\n"
        f"👷 Ijrochilar:\n"
        f"  ✅ Faol: {faol_ijrochilar}\n"
        f"  ⏳ Kutmoqda: {kutmoqda}\n"
        f"  📦 Jami: {len(ijrochilar)}",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
# PLATFORMA HAQIDA
# ─────────────────────────────────────────────
async def haqida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *ProClean Market haqida*\n\n"
        "Qarshi shahridagi professional tozalash xizmatlari platformasi.\n\n"
        "🧹 Xizmatlar:\n"
        "• Uy va ofis tozalash\n"
        "• Divan va gilam yuvish\n"
        "• Oyna tozalash\n"
        "• Remontdan keyingi tozalash\n\n"
        "📞 Aloqa: @admin_username\n"
        "📍 Qarshi, Qashqadaryo viloyati",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
# NOMA'LUM XABARLAR
# ─────────────────────────────────────────────
async def noma_lum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📋 Buyurtma berish"],
        ["👷 Ijrochi bo'lish"],
        ["ℹ️ Platforma haqida"],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Quyidagi tugmalardan foydalaning 👇",
        reply_markup=markup,
    )


# ─────────────────────────────────────────────
# ASOSIY — BOT ISHGA TUSHIRISH
# ─────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Mijoz buyurtma berish oqimi
    mijoz_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📋 Buyurtma berish$"), buyurtma_boshlash)],
        states={
            MIJOZ_XIZMAT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, mijoz_xizmat)],
            MIJOZ_XONA:       [MessageHandler(filters.TEXT & ~filters.COMMAND, mijoz_xona)],
            MIJOZ_MANZIL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, mijoz_manzil)],
            MIJOZ_TELEFON:    [MessageHandler(filters.TEXT & ~filters.COMMAND, mijoz_telefon)],
            MIJOZ_VAQT:       [MessageHandler(filters.TEXT & ~filters.COMMAND, mijoz_vaqt)],
            MIJOZ_TASDIQLASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, mijoz_tasdiqlash)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Ijrochi ro'yxatdan o'tish oqimi
    ijrochi_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^👷 Ijrochi bo'lish$"), ijrochi_royxat_boshlash)],
        states={
            IJROCHI_ISM:       [MessageHandler(filters.TEXT & ~filters.COMMAND, ijrochi_ism)],
            IJROCHI_TELEFON:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ijrochi_telefon)],
            IJROCHI_HUDUD:     [MessageHandler(filters.TEXT & ~filters.COMMAND, ijrochi_hudud)],
            IJROCHI_TASDIQLASH:[MessageHandler(filters.TEXT & ~filters.COMMAND, ijrochi_tasdiqlash)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(mijoz_conv)
    app.add_handler(ijrochi_conv)
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Platforma haqida$"), haqida))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, noma_lum))

    print("✅ ProClean Market boti ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
