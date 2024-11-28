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
    "I assert my dominance by whipping out my massive portfolio. When I go to a public restroom that has a person at a urinal, I go right next to them. No matter the age of the person, I stand back fairly far, about one and a half feet, just to make sure they can see my laptop with their peripheral vision. They almost always finish immediately. One time there was a swing trader at a urinal and I go to trade right next to him. I back step and turn on my Macbook Pro. The guy looks over as I open my Phantom. As I pull out my 9 fig $MD position, his jaw drops in amazement. I swear I saw him cum into the urinal as I started pissing. He finished up, went to wash his hands as I saw that his pants were covered in shit and cum. I felt proud of myself that day.",
    "\"Market dominance is the control of a economic market by a firm.\n\nA dominant firm possesses the power to affect competition and influence market price.\n\nAbuse of market dominance is an anti-competitive practice, however dominance itself is legal.\"\ndamn that bdsm sol token is breaking out",
    "\"Yes this is BDSM token why you ask?\n\n\n✧Big\n\n✧Dominate\n\n✧Some\n\n✧Markets\n\n\nദ്ദി・ᴗ・)✧\"",
    "MARKET WILL INCINERATE WEAKLINGS",
    "Oh, these? My boobies? My massive fucking titties? My super stuffed milkies? My honker bonker doinky boinkies? My fucking fabric stretching wind flapping gravity welling sex mounds? You mean these super duper ultra hyper god damn motherfucking tits?",
    "Everything I look at looks $MD coded. I look at CT posts and the AI dommy girl is looking back at me, taunting me. When I close my eyes to sleep I hear Creed singing for me. I look at another green dildo post, there it is. I look at BTC chart, it's right there. I can't escape it. Save me from this pain. My eyes are cursed by the deepest, darkest magic of Creation and I can't find a way to escape this endless suffering.",
    "Just for 1% market dominance $MD needs to reach ~$24.41 billion. Just 1% Do you understand the targets?",
    "To be fair, you have to have a very high IQ to understand Market Dominance. The humour is extremely subtle, and without a solid grasp of theoretical economics most of the jokes will go over a typical viewer's head. There's also the dom's monopolistic outlook, which is deftly woven into her character - her personal philosophy draws heavily from Adam Smith's literature, for instance. The fans understand this stuff; they have the intellectual capacity to truly appreciate the depths of these markets, to realize that they're not just profitable- they say something deep about ECONOMICS. As a consequence people who dislike $MD truly ARE submissive cucks - of course they wouldn't appreciate, for instance, the dominance in Viet Nam's catchphrase \"Nice bitch\" which itself is a cryptic reference to Vũ Trọng Phụng's Vietnamese epic \"Dumb Luck\". I'm smirking right now just imagining one of those addlepated simpletons scratching their heads in confusion as Billy Herrington's genius wit unfolds itself on their X timeline. What fools.. how I pity them. 😂 And yes, by the way, i DO have a MD tattoo. And no, you cannot see it. It's for the ladies' eyes only- and even then they have to demonstrate that they're in submissive position to my own beforehand. 😈👠"
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
