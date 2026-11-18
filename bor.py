import os
import random
import re
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import RetryAfter

# توکن رو از متغیر محیطی می‌خونیم
TOKEN = os.getenv("BOT_TOKEN")

WORDS = [
    "سلام", "خوبی", "چطوری", "امروز", "فردا", "دیروز", "کتاب", "موسیقی",
    "دریا", "کوه", "آسمان", "ستاره", "خورشید", "ماه", "ابر", "باران",
    "درخت", "گل", "پرنده", "ماهی", "شهر", "روستا", "جاده", "پنجره",
    "قهوه", "چای", "نان", "پنیر", "سیب", "پرتقال", "انار", "هندوانه",
    "دوست", "خانواده", "مدرسه", "دانشگاه", "کار", "خانه", "خیابان", "پارک",
]

MAX_COUNT = 500
ACTIVE = {}

async def is_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id, update.effective_user.id
        )
        return member.status in ("administrator", "creator")
    except Exception:
        return False

async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("❌ این دستور فقط در گروه کار می‌کند.")
        return

    if not await is_group_admin(update, context):
        await update.message.reply_text("❌ فقط ادمین‌های گروه می‌توانند از این دستور استفاده کنند.")
        return

    if ACTIVE.get(chat.id):
        await update.message.reply_text("⚠️ یک اسپم در حال اجراست. اول /cancel بزن.")
        return

    text = " ".join(context.args).strip()
    parts = re.split(r"[,\s]+", text)
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        await update.message.reply_text("📝 فرمت درست:\n/spam 150,1\n(تعداد، فاصله به ثانیه)")
        return

    count = int(parts[0])
    delay = float(parts[1])

    if not (1 <= count <= MAX_COUNT):
        await update.message.reply_text(f"❌ تعداد باید بین ۱ و {MAX_COUNT} باشد.")
        return
    if delay < 0.5:
        await update.message.reply_text("❌ حداقل فاصله 0.5 ثانیه است.")
        return

    ACTIVE[chat.id] = True
    await update.message.reply_text(f"🚀 شروع... {count} پیام با فاصله {delay} ثانیه")

    sent = 0
    try:
        for _ in range(count):
            if not ACTIVE.get(chat.id):
                await context.bot.send_message(chat.id, f"⏹ متوقف شد. {sent} پیام فرستاده شد.")
                return
            
            word = random.choice(WORDS)
            try:
                await context.bot.send_message(chat_id=chat.id, text=word)
                sent += 1
            except RetryAfter as e:
                wait_time = e.retry_after + 1
                await context.bot.send_message(
                    chat.id, f"⏳ محدودیت تلگرام. {wait_time} ثانیه صبر می‌کنم..."
                )
                await asyncio.sleep(wait_time)
                # بعد از صبر، دوباره تلاش می‌کنیم
                await context.bot.send_message(chat_id=chat.id, text=word)
                sent += 1
            
            await asyncio.sleep(delay)
    except Exception as e:
        await context.bot.send_message(chat.id, f"⚠️ متوقف شد در پیام {sent}: {e}")
        return
    finally:
        ACTIVE.pop(chat.id, None)

    await context.bot.send_message(chat.id, f"✅ تمام شد. {sent} پیام فرستاده شد.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not await is_group_admin(update, context):
        await update.message.reply_text("❌ فقط ادمین‌ها.")
        return
    if ACTIVE.get(chat.id):
        ACTIVE[chat.id] = False
        await update.message.reply_text("🛑 در حال توقف...")
    else:
        await update.message.reply_text("چیزی در حال اجرا نیست.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "دستورات:\n"
        "/spam 150,1 — ۱۵۰ پیام با فاصله ۱ ثانیه (فقط ادمین)\n"
        "/cancel — توقف اسپم در حال اجرا"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("cancel", cancel))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
