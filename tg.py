import os
import json
import logging
import requests
import telebot
from telebot import types
from environs import Env
from cachetools import TTLCache, cached
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StravaBot:
    def __init__(self):
        self.env = Env()
        self.env.read_env()
        
        # Bot configuration
        self.bot_token = self.env.str("BOT_TOKEN")
        self.group_id = self.env.str("GROUP_ID")
        self.club_id = self.env.str("CLUB_ID")
        self.donation_link = self.env.str("DONATION_LINK")
        
        # Initialize bot
        self.bot = telebot.TeleBot(self.bot_token)
        
        # Cache for 7 days (604800 seconds)
        self.cache = TTLCache(maxsize=100, ttl=7 * 24 * 60 * 60)
        
        # Setup handlers
        self._setup_handlers()
        
        # Start scheduler if enabled
        if self.env.bool("SCHEDULE"):
            self._start_scheduler()

    def load_cookies(self):
        """Load cookies from environment variable"""
        try:
            return json.loads(self.env.str("STRAVA_COOKIES"))
        except json.JSONDecodeError:
            logger.error("Error decoding STRAVA_COOKIES")
            return []

    def add_cookies_to_session(self, session, cookies):
        """Add cookies to session"""
        for cookie in cookies:
            session.cookies.set(cookie["name"], cookie["value"], domain=".strava.com")

    def get_top_athletes(self, url, metric):
        """Request data from Strava and cache for 7 days"""
        cache_key = f"{url}:{metric}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        try:
            session = requests.Session()
            cookies = self.load_cookies()
            self.add_cookies_to_session(session, cookies)

            headers = {
                'accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
                'x-requested-with': 'XMLHttpRequest'
            }
            response = session.get(url, headers=headers)
            response.raise_for_status()

            logger.debug(f"Full JSON response from Strava ({metric}):")
            logger.debug(json.dumps(response.json(), indent=4, ensure_ascii=False))

            data = response.json().get('data', [])
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error getting data from Strava: {e}")
            raise

    def format_message(self, top_athletes, metric):
        """Format message for specific metric"""
        try:
            emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            full_metric_names = {
                'distance': 'Distance',
                'elev_gain': 'Elevation Gain',
                'best_activities_distance': 'Longest Ride',
                'velocity': 'Speed'
            }
            message = f"Top 5 by {full_metric_names[metric]}:\n"
            sorted_athletes = sorted(top_athletes, key=lambda x: x[metric], reverse=True)[:5]
            for index, athlete in enumerate(sorted_athletes, start=1):
                name = f"[{athlete['athlete_firstname']} {athlete['athlete_lastname']}]({self.athlete_profile_url(athlete['athlete_id'])})"
                if metric == 'distance' or metric == 'best_activities_distance':
                    value = f"{athlete[metric] / 1000:.2f} km"
                elif metric == 'elev_gain':
                    value = f"{int(athlete[metric])} m"
                elif metric == 'velocity':
                    value = f"{athlete[metric] * 3.6:.2f} km/h"  # Convert speed to km/h
                else:
                    value = athlete[metric]
                rank_emoji = emoji[index - 1] if index <= 5 else str(index)
                message += f"{rank_emoji} {name}: {value}\n"
            return message
        except Exception as e:
            logger.error(f"Error in format_message: {e}")
            raise

    def athlete_profile_url(self, athlete_id):
        """Get athlete profile URL"""
        return f"https://www.strava.com/athletes/{athlete_id}"

    def format_combined_message(self):
        """Format combined message for all metrics"""
        try:
            message = "*Previous Week:*\n\n"
            metrics = {
                'distance': f'https://www.strava.com/clubs/{self.club_id}/leaderboard?week_offset=1&per_page=5&sort_by=distance',
                'elev_gain': f'https://www.strava.com/clubs/{self.club_id}/leaderboard?week_offset=1&per_page=5&sort_by=elev_gain',
                'best_activities_distance': f'https://www.strava.com/clubs/{self.club_id}/leaderboard?week_offset=1&per_page=5&sort_by=best_activities_distance',
                'velocity': f'https://www.strava.com/clubs/{self.club_id}/leaderboard?week_offset=1&per_page=5&sort_by=velocity'
            }
            for metric, url in metrics.items():
                top_athletes = self.get_top_athletes(url, metric)
                message += self.format_message(top_athletes, metric) + "\n"
            message += f"🚴[Strava Club Link](https://www.strava.com/clubs/{self.club_id}) | 🍻[Donate To Author]({self.donation_link})"
            return message
        except Exception as e:
            logger.error(f"Error in format_combined_message: {e}")
            raise

    def send_combined_message(self, chat_id):
        """Send combined message to chat"""
        try:
            response_message = self.format_combined_message()
            if self.env.bool("IMAGE"):
                image_url = self.env.str("IMAGE_URL")
                self.bot.send_photo(chat_id, image_url, caption=response_message, parse_mode='Markdown')
            else:
                self.bot.send_message(chat_id, response_message, parse_mode='Markdown', disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"Error in send_combined_message: {e}")
            raise

    def send_weekly_message(self):
        """Send weekly message to group"""
        try:
            self.send_combined_message(self.group_id)
        except Exception as e:
            logger.error(f"Error in send_weekly_message: {e}")
            raise

    def _setup_handlers(self):
        """Setup bot command handlers"""
        
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            try:
                welcome_message = """
Hello! I am the Strava Club Weekly Top Bot. 🚴‍♂️🏅
Use /weektop to get the top 5 club members of the week by distance, elevation gain, longest ride, and speed.
You can also use me in inline mode for quick access.

Need help or have questions? Feel free to PM @iceflame.

[View Source Code](https://github.com/DmitryTeplov182/strava-club-leatherboard-bot) | [Donate To Author](https://telegra.ph/Donaty-na-server-10-21)
"""
                self.bot.reply_to(message, welcome_message, parse_mode='Markdown', disable_web_page_preview=True)
            except Exception as e:
                logger.error(f"Error in send_welcome: {e}")
                raise

        @self.bot.message_handler(commands=['weektop'])
        def send_week_top(message):
            try:
                self.send_combined_message(message.chat.id)
            except Exception as e:
                logger.error(f"Error in send_week_top: {e}")
                raise

        @self.bot.inline_handler(lambda query: True)
        def inline_query(query):
            try:
                results = [types.InlineQueryResultArticle(
                    id='1',
                    title="Top 5 Club Members",
                    description="Click to see the top 5 club members by various metrics",
                    input_message_content=types.InputTextMessageContent(
                        self.format_combined_message(),
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                )]
                self.bot.answer_inline_query(query.id, results)
            except Exception as e:
                logger.error(f"Error in inline_query: {e}")
                raise

    def _start_scheduler(self):
        """Start scheduler for weekly messages"""
        if self.env.bool("SCHEDULE"):
            scheduler = BackgroundScheduler()
            weekday = self.env.str("WEEKDAY")
            send_time = self.env.str("SEND_TIME")
            scheduler.add_job(
                self.send_weekly_message, 
                'cron', 
                day_of_week=weekday, 
                hour=int(send_time.split(":")[0]), 
                minute=int(send_time.split(":")[1])
            )
            scheduler.start()
            logger.info(f"Scheduler started for {weekday} at {send_time}")

    def run(self):
        """Start the bot"""
        logger.info("Starting Strava Bot...")
        self.bot.polling()


def main():
    """Main entry point"""
    bot = StravaBot()
    bot.run()


if __name__ == "__main__":
    main()