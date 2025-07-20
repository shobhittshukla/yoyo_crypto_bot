import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Replace with your actual Telegram bot token
TELEGRAM_BOT_TOKEN = "7666636981:AAEjoz__qGOB5HkZUZR69afKThU-rTqHGI4"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionary to store user alerts in format: {chat_id: [(symbol, target_price, direction)]}
user_alerts = {}

# Function to get the live price of a symbol from Binance
async def get_price(symbol: str) -> float:
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return float(data['price'])

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Crypto Alert Bot!\nUse /setalert SYMBOL TARGET_DIRECTION (e.g., /setalert BTCUSDT 65000 above)")

# Command: /setalert BTCUSDT 65000 above
async def setalert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        symbol = context.args[0].upper()
        target = float(context.args[1])
        direction = context.args[2].lower()
        if direction not in ["above", "below"]:
            raise ValueError("Direction must be 'above' or 'below'")

        if chat_id not in user_alerts:
            user_alerts[chat_id] = []
        user_alerts[chat_id].append((symbol, target, direction))

        await update.message.reply_text(f"Alert set for {symbol} to go {direction} {target}")
        logger.info(f"Set alert: {chat_id}: {symbol} {direction} {target}")

    except (IndexError, ValueError) as e:
        await update.message.reply_text("Usage: /setalert SYMBOL TARGET_PRICE DIRECTION (above/below)")

# Background task to check alerts and send messages
async def check_alerts(application):
    while True:
        try:
            for chat_id, alerts in list(user_alerts.items()):
                for alert in alerts[:]:  # copy to avoid mutation issues
                    symbol, target_price, direction = alert
                    try:
                        price = await get_price(symbol)
                        condition_met = (direction == "above" and price >= target_price) or \
                                        (direction == "below" and price <= target_price)
                        if condition_met:
                            await application.bot.send_message(
                                chat_id=chat_id,
                                text=f"🚨 Alert! {symbol} is now at {price} ({direction} {target_price})"
                            )
                            alerts.remove(alert)
                    except Exception as e:
                        logger.error(f"Error fetching price for {symbol}: {e}")
        except Exception as e:
            logger.exception("Error checking alerts")

        await asyncio.sleep(10)  # check every 10 seconds

async def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setalert", setalert))

    # Start background task
    asyncio.create_task(check_alerts(application))

    logger.info("Bot started")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
