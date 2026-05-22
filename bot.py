import logging
import asyncio
import re
import httpx
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
AFFILIATE_LINK = os.environ.get("AFFILIATE_LINK")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_to_affiliate(url: str) -> str:
    match = re.search(r'/item/(\d+)', url)
    if match:
        return f"https://s.click.aliexpress.com/e/_c3t8tGfL?productId={match.group(1)}"
    return AFFILIATE_LINK

async def post_product(bot, title, url, price=""):
    affiliate_url = convert_to_affiliate(url)
    message = f"🛒 *{title}*\n\n💰 السعر: {price if price else 'اضغط للتحقق'}\n\n🔥 عرض محدود لا تفوته!"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ اشتري الآن", url=affiliate_url)],
        [InlineKeyboardButton("📦 المزيد من العروض", url=AFFILIATE_LINK)]
    ])
    await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown", reply_markup=keyboard)

async def start(update, context):
    await update.message.reply_text(
        "👋 أهلاً! أنا بوت AliExpress\n\n"
        "أرسل لي أي رابط منتج من AliExpress وأحوله لرابط عمولتك وأنشره في القناة!"
    )

async def handle_url(update, context):
    text = update.message.text
    if "aliexpress.com" in text:
        affiliate_url = convert_to_affiliate(text)
        await update.message.reply_text(
            f"✅ رابط العمولة جاهز!\n\n`{affiliate_url}`\n\nهل تنشره في القناة؟",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ نشر الآن", callback_data=f"pub:{affiliate_url}")]
            ])
        )
    else:
        await update.message.reply_text("❌ أرسل رابط منتج من AliExpress")

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("pub:"):
        url = query.data.replace("pub:", "")
        await post_product(context.bot, "🔥 عرض خاص من AliExpress", url)
        await query.edit_message_text("✅ تم النشر في القناة!")

async def auto_post(bot):
    message = "🌟 *عروض AliExpress اليوم!*\n\n🛍️ أفضل المنتجات بأسعار لا تُصدق!\n\n⏰ عروض محدودة!"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 تسوق الآن", url=AFFILIATE_LINK)]
    ])
    await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown", reply_markup=keyboard)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(auto_post, 'interval', hours=6, args=[app.bot])
    scheduler.start()
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
