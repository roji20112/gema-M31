import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

SERVICES = {
    "cars": "🚗 سيارات CPM\n\n• سيارة عادية: 100\n• سيارة نادرة: 200\n• سيارة VIP: 300",
    "money": "💰 Money / Coins\n\n• 1M Money: 100\n• 5M Money: 300\n• 10M Money: 500",
    "tuning": "🎨 Tuning\n\n• تعديل كامل: 200\n• لون خاص: 100\n• Performance: 150",
}


def menu():
    keyboard = [
        [
            InlineKeyboardButton("🚗 السيارات", callback_data="cars"),
            InlineKeyboardButton("💰 Money", callback_data="money"),
        ],
        [
            InlineKeyboardButton("🎨 Tuning", callback_data="tuning"),
            InlineKeyboardButton("💵 الأسعار", callback_data="prices"),
        ],
        [
            InlineKeyboardButton("📦 طلب خدمة", callback_data="order"),
        ],
        [
            InlineKeyboardButton("📞 الدعم", callback_data="support"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚗 أهلاً بك في CPM Services\n\n"
        "🔥 بوت خدمات Car Parking Multiplayer\n\n"
        "اختار الخدمة التي تريدها من القائمة:"
    )

    await update.message.reply_text(text, reply_markup=menu())


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in SERVICES:
        await query.edit_message_text(
            SERVICES[query.data],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 طلب هذه الخدمة", callback_data="order")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ])
        )

    elif query.data == "prices":
        await query.edit_message_text(
            "💵 قائمة الأسعار\n\n"
            "🚗 السيارات: ابتداءً من 100\n"
            "💰 Money: ابتداءً من 100\n"
            "🎨 Tuning: ابتداءً من 100\n\n"
            "📦 الأسعار قابلة للتغيير حسب الطلب.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 طلب خدمة", callback_data="order")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ])
        )

    elif query.data == "order":
        await query.edit_message_text(
            "📦 لطلب خدمة:\n\n"
            "أرسل للإدارة المعلومات التالية:\n"
            "• اسمك\n"
            "• ID الخاص بك في CPM\n"
            "• الخدمة التي تريدها\n"
            "• تفاصيل الطلب\n\n"
            "📞 تواصل مع الإدارة لإكمال الطلب.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ])
        )

    elif query.data == "support":
        await query.edit_message_text(
            "📞 الدعم\n\n"
            "إذا عندك مشكلة أو تريد طلب خدمة، تواصل مع الإدارة.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ])
        )

    elif query.data == "back":
        await query.edit_message_text(
            "🚗 CPM Services\n\nاختار الخدمة:",
            reply_markup=menu()
        )


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN غير موجود")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("CPM Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()