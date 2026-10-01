import os
import re
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# أنماط شائعة للأوامر داخل ملفات Lua
PATTERNS = [
    r'["\'](/[\w_:-]+)["\']',
    r'command\s*=\s*["\']([^"\']+)["\']',
    r'cmd\s*=\s*["\']([^"\']+)["\']',
    r'commands?\s*\[\s*["\']([^"\']+)["\']\s*\]',
]


def extract_commands(code):
    commands = set()

    for pattern in PATTERNS:
        for match in re.findall(pattern, code, re.IGNORECASE):
            command = match.strip()

            if command.startswith("/"):
                commands.add(command)

    return sorted(commands)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Lua Command Extractor\n\n"
        "📂 أرسل لي ملف Lua (.lua)\n"
        "وسأستخرج الأوامر الموجودة داخله.\n\n"
        "⚠️ لن أقوم بتشغيل الملف."
    )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document:
        return

    filename = document.file_name or ""

    if not filename.lower().endswith(".lua"):
        await update.message.reply_text(
            "❌ أرسل ملف بصيغة .lua فقط."
        )
        return

    if document.file_size and document.file_size > 2 * 1024 * 1024:
        await update.message.reply_text(
            "❌ الملف كبير جداً. الحد الأقصى 2MB."
        )
        return

    status = await update.message.reply_text("🔍 جاري تحليل الملف...")

    try:
        tg_file = await document.get_file()
        data = await tg_file.download_as_bytearray()

        code = bytes(data).decode("utf-8", errors="ignore")

        commands = extract_commands(code)

        if not commands:
            await status.edit_text(
                "⚠️ ما لقيتش أوامر واضحة داخل الملف."
            )
            return

        result = "📋 الأوامر الموجودة:\n\n"

        for i, command in enumerate(commands, 1):
            result += f"{i}. `{command}`\n"

        # Telegram message limit
        if len(result) <= 4000:
            await status.edit_text(
                result,
                parse_mode="Markdown"
            )
        else:
            await status.edit_text(
                f"✅ تم العثور على {len(commands)} أمر.\n"
                "📄 أرسلتلك القائمة في ملف."
            )

        txt = "\n".join(commands)
        filename_out = "lua_commands.txt"

        with open(filename_out, "w", encoding="utf-8") as f:
            f.write(txt)

        with open(filename_out, "rb") as f:
            await update.message.reply_document(
                document=f,
                caption=f"📄 {len(commands)} أمر مستخرج من {filename}"
            )

        os.remove(filename_out)

    except Exception as e:
        logging.exception(e)

        await status.edit_text(
            "❌ حدث خطأ أثناء تحليل الملف."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 طريقة الاستخدام:\n\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n\n"
        "ثم أرسل ملف .lua."
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود في Environment Variables"
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            handle_file
        )
    )

    print("🤖 Lua Command Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()