import os
import random
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

class MarketDataCache:
    def __init__(self, cache_duration=600):
        self.cache_duration = cache_duration
        self.last_update = None
        self.fdv = None
        self.total_market_cap = None
        
    async def get_market_data(self):
        current_time = datetime.now()
        
        if (self.last_update is None or 
            current_time - self.last_update > timedelta(seconds=self.cache_duration)):
            
            try:
                # Fetch total market cap
                global_response = requests.get('https://api.coingecko.com/api/v3/global')
                global_data = global_response.json()
                self.total_market_cap = global_data['data']['total_market_cap']['usd']
                
                # Fetch market-dominance token data
                token_response = requests.get(
                    'https://api.coingecko.com/api/v3/coins/market-dominance',
                    params={
                        'localization': 'false',
                        'tickers': 'false',
                        'market_data': 'true',
                        'community_data': 'false',
                        'developer_data': 'false'
                    }
                )
                token_data = token_response.json()
                self.fdv = token_data['market_data']['fully_diluted_valuation']['usd']
                
                self.last_update = current_time
                logging.info(f"Updated cache - FDV: ${self.fdv:,.2f}, Total Market Cap: ${self.total_market_cap:,.2f}")
                
            except Exception as e:
                logging.error(f"Error fetching data: {e}")
                if self.total_market_cap is None or self.fdv is None:
                    raise
        
        return self.fdv, self.total_market_cap

market_cache = MarketDataCache()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "👋 Welcome! I'm a Market Dominance Bot.\n\n"
        "Commands:\n"
        "/dominance - Check current market dominance\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "📊 *Available Commands*\n\n"
        "/dominance - Check current market dominance\n"
        "/help - Show this help message\n\n"
        "Data is updated every 10 minutes."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def dominance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        fdv, total_market_cap = await market_cache.get_market_data()
        dominance = (fdv / total_market_cap) * 100
        
        response = (
            "📊 *Market Dominance Report*\n\n"
            f"Dominance (FDV): `{dominance:.8f}%`\n"
            f"Token FDV: `${fdv:,.2f}`\n"
            f"Total Market Cap: `${total_market_cap:,.2f}`\n"
            f"Last Updated: `{market_cache.last_update.strftime('%Y-%m-%d %H:%M:%S UTC')}`"
        )
        
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logging.error(f"Error in dominance command: {e}")
        await update.message.reply_text(
            "❌ Error calculating market dominance. Please try again later."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if the message exists and is from a non-bot user
    if update.message and not update.message.from_user.is_bot:
        if 'dominance' in update.message.text.lower():
            await update.message.reply_text(random.choice(messages))
        # 30% chance to respond with "hahaha"
        elif random.random() < 0.30:
            await update.message.reply_text('shut up, I am your Domina little cuck')

messages = [
    "I believe Market Dominance is the most innovative memecoin ever developed",
    "Market dominance is the control of a economic market by a firm.",
    "MARKET WILL INCINERATE WEAKLINGS",
    "Just for 1% market dominance $MD needs to reach ~$24.41 billion. Just 1% Do you understand the targets?",
]

def main():
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("dominance", dominance_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    print("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error running bot: {e}")
