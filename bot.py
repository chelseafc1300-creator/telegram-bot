import os
import logging
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ======================
# TOKEN
# ======================
TOKEN = os.getenv("8718071237:AAEZJxHBlXXe1XGv0ztqxsNuPqUb_9iSnK8", "PUT_YOUR_TOKEN_HERE")

# ======================
# LOG
# ======================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ======================
# BINANCE API
# ======================
def get_price(symbol: str):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        r = requests.get(url, timeout=10)
        return float(r.json()["price"])
    except:
        return None


def get_rsi(symbol: str):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=20"
        data = requests.get(url, timeout=10).json()

        closes = [float(i[4]) for i in data]

        gains, losses = [], []

        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))

        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    except:
        return None

# ======================
# UI BUTTONS
# ======================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 قیمت BTC", callback_data="price_BTCUSDT")],
        [InlineKeyboardButton("📊 قیمت ETH", callback_data="price_ETHUSDT")],
        [InlineKeyboardButton("📡 سیگنال BTC", callback_data="signal_BTCUSDT")],
        [InlineKeyboardButton("📡 سیگنال ETH", callback_data="signal_ETHUSDT")]
    ])

# ======================
# START (فقط UI)
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 ربات سیگنال فعال شد\n\n"
        "از دکمه‌ها استفاده کن 👇",
        reply_markup=main_menu()
    )

# ======================
# CALLBACK HANDLER
# ======================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # ------------------
    # PRICE
    # ------------------
    if data.startswith("price_"):
        symbol = data.replace("price_", "")
        price = get_price(symbol)

        if price:
            text = f"📊 {symbol}\n💰 Price: {price}"
        else:
            text = "❌ خطا در دریافت قیمت"

        await query.edit_message_text(text, reply_markup=main_menu())

    # ------------------
    # SIGNAL
    # ------------------
    elif data.startswith("signal_"):
        symbol = data.replace("signal_", "")

        price = get_price(symbol)
        rsi = get_rsi(symbol)

        if not price or rsi is None:
            await query.edit_message_text("❌ خطا در دریافت دیتا", reply_markup=main_menu())
            return

        if rsi < 30:
            direction = "LONG 🟢"
        elif rsi > 70:
            direction = "SHORT 🔴"
        else:
            direction = "NO TRADE ⚪"

        tp = round(price * 1.02, 2)
        sl = round(price * 0.98, 2)

        text = f"""
📡 SIGNAL {symbol}

💰 Price: {price}
📊 RSI: {rsi}

➡️ Direction: {direction}

🎯 TP: {tp}
🛑 SL: {sl}
"""

        await query.edit_message_text(text, reply_markup=main_menu())

# ======================
# MAIN
# ======================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
