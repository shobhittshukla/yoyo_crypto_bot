import logging
import asyncio
import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ✅ Global alert list
alerts = []

# ✅ Fetch price from Binance
async def fetch_price(symbol: str) -> float:
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return float(data["price"])
    except Exception as e:
        logger.error(f"Failed to fetch price: {e}")
        return 0.0

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Crypto Alert Bot!\n\n"
        "Use /setalert <symbol> <above|below> <price>\n"
        "Example: /setalert BTCUSDT above 60000"
    )

# ✅ /setalert command
async def set_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 3:
            await update.message.reply_text("❌ Usage: /setalert <symbol> <above|below> <price>")
            return

        symbol, direction, price = context.args
        price = float(price)
        if direction not in ["above", "below"]:
            await update.message.reply_text("❌ Direction must be 'above' or 'below'")
            return

        alert = {
            "chat_id": update.effective_chat.id,
            "symbol": symbol.upper(),
            "target_price": price,
            "direction": direction
        }

        alerts.append(alert)

        await update.message.reply_text(
            f"✅ Alert set for {symbol.upper()} {direction} {price}"
        )

    except Exception as e:
        logger.exception("Error in /setalert")
        await update.message.reply_text("⚠️ Failed to set alert. Please try again.")

# ✅ Check alerts loop
async def check_alerts(application):
    while True:
        try:
            for alert in alerts.copy():
                chat_id = alert["chat_id"]
                symbol = alert["symbol"]
                target_price = alert["target_price"]
                direction = alert["direction"]

                price = await fetch_price(symbol)

                if (direction == "above" and price > target_price) or \
                   (direction == "below" and price < target_price):
                    await application.bot.send_message(
                        chat_id=chat_id,
                        text=f"🚨 Alert! {symbol} is now at {price} ({direction} {target_price})"
                    )
                    alerts.remove(alert)

        except Exception as e:
            logger.exception("Error in alert checker")

        await asyncio.sleep(10)

# ✅ Main function
async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN ")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables.")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setalert", set_alert))

    # Start alert checking loop
    asyncio.create_task(check_alerts(application))

    print("✅ Bot is running...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

            
  
