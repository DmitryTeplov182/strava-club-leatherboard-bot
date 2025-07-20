import os
import json
import requests
import telebot
from telebot import types
from environs import Env
from cachetools import TTLCache, cached
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread

env = Env()
env.read_env()

# Telegram Bot
bot_token = env.str("BOT_TOKEN")
group_id = env.str("GROUP_ID")
bot = telebot.TeleBot(bot_token)

# Кеш на 7 дней (604800 секунд)
cache = TTLCache(maxsize=100, ttl=7 * 24 * 60 * 60)

def load_cookies():
    """Загружаем куки из переменной окружения"""
    try:
        return json.loads(env.str("STRAVA_COOKIES"))
    except json.JSONDecodeError:
        print("[ERROR] Ошибка декодирования STRAVA_COOKIES")
        return []

def add_cookies_to_session(session, cookies):
    """Добавляем куки в сессию"""
    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"], domain=".strava.com")

@cached(cache)
def get_top_athletes(url, metric):
    """Запрашиваем данные у Strava и кешируем на 7 дней"""
    try:
        session = requests.Session()
        cookies = load_cookies()
        add_cookies_to_session(session, cookies)

        headers = {
            'accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
            'x-requested-with': 'XMLHttpRequest'
        }
        response = session.get(url, headers=headers)
        response.raise_for_status()

        print(f"[DEBUG] Полный JSON-ответ от Strava ({metric}):")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))

        return response.json().get('data', [])
    except Exception as e:
        print(f"[ERROR] Ошибка при получении данных со Strava: {e}")
        raise

def format_message(top_athletes, metric):
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
            name = f"[{athlete['athlete_firstname']} {athlete['athlete_lastname']}]({athlete_profile_url(athlete['athlete_id'])})"
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
        print(f"Error in format_message: {e}")
        raise

# Helper function to get athlete profile URL
def athlete_profile_url(athlete_id):
    return f"https://www.strava.com/athletes/{athlete_id}"

# Function to format the combined message for all metrics
def format_combined_message():
    try:
        message = "*Previous Week:*\n\n"
        club_id = env.str("CLUB_ID")
        donation_link = env.str("DONATION_LINK")
        metrics = {
            'distance': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=distance',
            'elev_gain': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=elev_gain',
            'best_activities_distance': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=best_activities_distance',
            'velocity': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=velocity'
        }
        for metric, url in metrics.items():
            top_athletes = get_top_athletes(url, metric)
            message += format_message(top_athletes, metric) + "\n"
        message += f"🚴[Strava Club Link](https://www.strava.com/clubs/{club_id}) | 🍻[Donate To Author]({donation_link}) | 🤖[Komoot To GPX Bot](https://t.me/komoot_to_gpx_bot)"
        return message
    except Exception as e:
        print(f"Error in format_combined_message: {e}")
        raise

# Initialize Telegram bot
bot_token = env.str("BOT_TOKEN")
group_id = env.str("GROUP_ID")
bot = telebot.TeleBot(bot_token)

# Command handler for /start and /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        welcome_message = """
Hello! I am the Strava Club Weekly Top Bot. 🚴‍♂️🏅
Use /weektop to get the top 5 club members of the week by distance, elevation gain, longest ride, and speed.
You can also use me in inline mode for quick access.

Need help or have questions? Feel free to PM @iceflame.

[View Source Code](https://github.com/DmitryTeplov182/strava-club-leatherboard-bot) | [Donate To Author](https://telegra.ph/Donaty-na-server-10-21)
"""
        bot.reply_to(message, welcome_message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        print(f"Error in send_welcome: {e}")
        raise

# Command handler for /weektop
@bot.message_handler(commands=['weektop'])
def send_week_top(message):
    try:
        send_combined_message(message.chat.id)
    except Exception as e:
        print(f"Error in send_week_top: {e}")
        raise

# Inline query handler
@bot.inline_handler(lambda query: True)
def inline_query(query):
    try:
        results = [types.InlineQueryResultArticle(
            id='1',
            title="Top 5 Club Members",
            description="Click to see the top 5 club members by various metrics",
            input_message_content=types.InputTextMessageContent(
                format_combined_message(),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        )]
        bot.answer_inline_query(query.id, results)
    except Exception as e:
        print(f"Error in inline_query: {e}")
        raise

# Function to send the combined message
def send_combined_message(chat_id):
    try:
        response_message = format_combined_message()
        if env.bool("IMAGE"):
            image_url = env.str("IMAGE_URL")
            bot.send_photo(chat_id, image_url, caption=response_message, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, response_message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        print(f"Error in send_combined_message: {e}")
        raise

# Function to send the weekly message
def send_weekly_message():
    try:
        send_combined_message(group_id)
    except Exception as e:
        print(f"Error in send_weekly_message: {e}")
        raise

# Function to schedule the weekly message
def schedule_weekly_message():
    if env.bool("SCHEDULE"):
        scheduler = BackgroundScheduler()
        weekday = env.str("WEEKDAY")
        send_time = env.str("SEND_TIME")
        scheduler.add_job(send_weekly_message, 'cron', day_of_week=weekday, hour=int(send_time.split(":")[0]), minute=int(send_time.split(":")[1]))
        scheduler.start()

# Start the scheduler thread if scheduling is enabled
if env.bool("SCHEDULE"):
    thread = Thread(target=schedule_weekly_message)
    thread.start()

bot.polling()