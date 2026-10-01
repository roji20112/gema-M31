import os
import re
import logging
from io import BytesIO

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BufferedInputFile,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("📂 تحليل Lua", callback_data="analyze"),
            InlineKeyboardButton("📋 الأوامر", callback_data="commands"),
        ],
        [
            InlineKeyboardButton("ℹ️ المساعدة", callback_data="help"),
            InlineKeyboardButton("🤖 حول البوت", callback_data="about"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def extract_commands(code: str):
    commands = set()

    patterns = [
        # "/command"
        r'["\'](/[\w-]+)["\']',

        # command = "/command"
        r'\bcommand\s*=\s*["\']([^"\']+)["\']',

        # cmd = "/command"
        r'\bcmd\s*=\s*["\']([^"\']+)["\']',

        # Commands["/command"]
        r'[Cc]ommands?\s*\[\s*["\']([^"\']+)["\']\s*\]',

        # RegisterCommand("/command")
        r'[Rr]egisterCommand\s*\(\s*["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, code)

        for command in matches:
            command = command.strip()

            if command.startswith("/"):
                commands.add(command)

    return sorted(commands, key=str.lower)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *Lua Command Bot*\n\n"
        "أهلاً بك 👋\n"
        "أرسل ملف `.lua` وسأبحث عن الأوامر الموجودة داخله.\n\n"
        "⚠️ البوت يقوم بتحليل الملف فقط ولا يقوم بتشغيل كود Lua."
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *طريقة الاستخدام*\n\n"
        "1️⃣ اضغط 📂 تحليل Lua\n"
        "2️⃣ أرسل ملف `.lua`\n"
        "3️⃣ انتظر التحليل\n"
        "4️⃣ تحصل على قائمة الأوامر وملف TXT\n\n"
        "📦 الحد الأقصى للملف: 5MB",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if query.data == "analyze":
        await query.edit_message_text(
            "📂 *تحليل Lua*\n\n"
            "أرسل الآن ملف `.lua` هنا.\n\n"
            "⚠️ لن يتم تشغيل الملف.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="home")]
            ]),
        )

    elif query.data == "commands":
        await query.edit_message_text(
            "📋 *استخراج الأوامر*\n\n"
            "أرسل ملف Lua وسأبحث عن الأوامر مثل:\n\n"
            "`/menu`\n"
            "`/spawn`\n"
            "`/car`\n"
            "`/money`\n\n"
            "ثم أرسلها لك في قائمة وملف TXT.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📂 تحليل ملف", callback_data="analyze")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="home")],
            ]),
        )

    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ *المساعدة*\n\n"
            "• أرسل ملف Lua فقط\n"
            "• الحد الأقصى 5MB\n"
            "• يتم استخراج الأوامر فقط\n"
            "• لا يتم تشغيل Lua على السيرفر",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="home")]
            ]),
        )

    elif query.data == "about":
        await query.edit_message_text(
            "🤖 *Lua Command Bot*\n\n"
            "بوت لتحليل ملفات Lua واستخراج الأوامر منها.\n\n"
            "🔐 لا يقوم بتنفيذ الملفات.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="home")]
            ]),
        )

    elif query.data == "home":
        await query.edit_message_text(
            "🤖 *Lua Command Bot*\n\nاختر من القائمة:",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )


async def handle_lua_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    document = update.message.document

    if not document:
        return

    filename = document.file_name or "unknown.lua"

    if not filename.lower().endswith(".lua"):
        await update.message.reply_text(
            "❌ الملف لازم يكون بصيغة `.lua`.",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )
        return

    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await update.message.reply_text(
            "❌ حجم الملف كبير جداً.\n\nالحد الأقصى: 5MB.",
            reply_markup=main_menu(),
        )
        return

    status = await update.message.reply_text(
        "🔍 جاري تحليل ملف Lua..."
    )

    try:
        telegram_file = await document.get_file()
        data = await telegram_file.download_as_bytearray()

        code = bytes(data).decode(
            "utf-8",
            errors="ignore",
        )

        commands = extract_commands(code)

        if not commands:
            await status.edit_text(
                "⚠️ لم أجد أوامر واضحة داخل الملف.\n\n"
                "يمكن أن تكون الأوامر مكتوبة بطريقة مختلفة."
            )
            return

        text = (
            f"✅ *تم تحليل الملف*\n\n"
            f"📄 الملف: `{filename}`\n"
            f"📋 عدد الأوامر: *{len(commands)}*\n\n"
        )

        # Telegram message limit
        for number, command in enumerate(commands, 1):
            line = f"{number}. `{command}`\n"

            if len(text) + len(line) > 3800:
                text += "\n📄 القائمة الكاملة موجودة في الملف TXT."
                break

            text += line

        await status.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )

        txt_content = "\n".join(commands)
        txt_bytes = txt_content.encode("utf-8")

        output = BufferedInputFile(
            txt_bytes,
            filename="lua_commands.txt",
        )

        await update.message.reply_document(
            document=output,
            caption=f"📋 {len(commands)} أمر مستخرج من {filename}",
        )

    except Exception:
        logging.exception("Lua analysis error")

        await status.edit_text(
            "❌ حدث خطأ أثناء تحليل الملف.\n"
            "حاول إرسال الملف مرة أخرى."
        )


async def unknown_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "👋 استعمل الأزرار الموجودة في القائمة أو أرسل ملف `.lua`.",
        reply_markup=main_menu(),
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود في Environment Variables."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            handle_lua_file,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND & ~filters.Document.ALL,
            unknown_message,
        )
    )

    print("🤖 Lua Command Bot started")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()