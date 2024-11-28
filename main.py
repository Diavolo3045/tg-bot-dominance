import os
import time
import requests
import logging
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import Application, CommandHandler, ContextTypes, ChatMemberHandler
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Enable logging
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
                
                # Fetch market-dominance token data using FDV
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

# Initialize cache as a global variable
market_cache = MarketDataCache()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        message = (
            "👋 Welcome! I'm a Market Dominance Bot.\n\n"
            "Commands:\n"
            "/dominance - Check current market dominance\n"
            "/help - Show this help message"
        )
    else:
        message = (
            "👋 Bot added to group!\n\n"
            "Commands:\n"
            "/dominance - Check current market dominance\n"
            "/help - Show available commands"
        )
    
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_text = (
        "📊 *Available Commands*\n\n"
        "/dominance - Check current market dominance\n"
        "/help - Show this help message\n\n"
        "You can use these commands in private chat or in groups.\n"
        "Data is updated every 10 minutes."
    )
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def dominance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send market dominance information using FDV."""
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

async def handle_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bot being added to or removed from a group."""
    result = update.chat_member
    
    if result.new_chat_member.user.id == context.bot.id:  # Bot's own status changed
        if result.new_chat_member.status in ["member", "administrator"]:
            logging.info(f"Bot added to group: {update.effective_chat.title}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Thanks for adding me! Use /help to see available commands."
            )

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("dominance", dominance))
    application.add_handler(ChatMemberHandler(handle_member_update, ChatMemberUpdated))

    # Run the bot until the user presses Ctrl-C
    print("Bot started. Press Ctrl+C to stop.")
    application.run_polling(stop_signals=None)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error running bot: {e}")
