import os
import telebot
from telebot import types
import json
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import time
from threading import Thread
from environs import Env

env = Env()
env.read_env()

def parse_value(value):
    try:
        return float(value)
    except Exception as e:
        print(f"Error in parse_value: {e}")
        raise

def get_top_athletes(url, metric):
    try:
        headers = {
            'accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
            'x-requested-with': 'XMLHttpRequest'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        athletes = response.json().get('data', [])
        if metric == 'longest':
            for athlete in athletes:
                athlete['longest'] = athlete.get('best_activities_distance', 0)
        return athletes
    except Exception as e:
        print(f"Error in get_top_athletes: {e}")
        raise

def format_message(top_athletes, metric):
    try:
        emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        full_metric_names = {
            'distance': 'Distance',
            'elev_gain': 'Elevation Gain',
            'longest': 'Longest Ride'
        }
        message = f"Top 5 by {full_metric_names[metric]}:\n"
        for index, athlete in enumerate(top_athletes, start=1):
            name = f"[{athlete['athlete_firstname']} {athlete['athlete_lastname']}]({athlete_profile_url(athlete['athlete_id'])})"
            if metric == 'distance' or metric == 'longest':
                value = f"{athlete[metric] / 1000:.2f} km"
            elif metric == 'elev_gain':
                value = f"{int(athlete[metric])} m"
            else:
                value = athlete[metric]
            rank_emoji = emoji[index - 1] if index <= 5 else str(index)
            message += f"{rank_emoji} {name}: {value}\n"
        return message
    except Exception as e:
        print(f"Error in format_message: {e}")
        raise

def athlete_profile_url(athlete_id):
    return f"https://www.strava.com/athletes/{athlete_id}"

def format_combined_message():
    try:
        message = "*Previous Week:*\n\n"
        club_id = env.str("CLUB_ID")
        metrics = {
            'distance': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=distance',
            'elev_gain': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=elev_gain',
            'longest': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=distance'
        }
        for metric, url in metrics.items():
            top_athletes = get_top_athletes(url, metric)
            message += format_message(top_athletes, metric) + "\n"
        message += f"[Strava Club Link](https://www.strava.com/clubs/{club_id})"
        return message
    except Exception as e:
        print(f"Error in format_combined_message: {e}")
        raise

bot_token = env.str("BOT_TOKEN")
group_id = env.str("GROUP_ID")
bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        welcome_message = """
Hello! I am the Strava Club Weekly Top Bot. 🚴‍♂️🏅
Use /weektop to get the top 5 club members of the week by distance, elevation gain, and longest ride.
You can also use me in inline mode for quick access.

Need help or have questions? Feel free to PM @iceflame.

[View Source Code](https://github.com/DmitryTeplov182/strava-club-leatherboard-bot)
"""
        bot.reply_to(message, welcome_message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        print(f"Error in send_welcome: {e}")
        raise

@bot.message_handler(commands=['weektop'])
def send_week_top(message):
    try:
        send_combined_message(message.chat.id)
    except Exception as e:
        print(f"Error in send_week_top: {e}")
        raise

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

def send_combined_message(chat_id):
    try:
        response_message = format_combined_message()
        if env.bool("IMAGE"):
            image_path = env.str("IMAGE_PATH")
            with open(image_path, 'rb') as image_file:
                bot.send_photo(chat_id, image_file, caption=response_message, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, response_message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        print(f"Error in send_combined_message: {e}")
        raise

def send_weekly_message():
    try:
        send_combined_message(group_id)
    except Exception as e:
        print(f"Error in send_weekly_message: {e}")
        raise

def schedule_weekly_message():
    if env.bool("SCHEDULE"):
        scheduler = BackgroundScheduler()
        weekday = env.str("WEEKDAY")
        send_time = env.str("SEND_TIME")
        scheduler.add_job(send_weekly_message, 'cron', day_of_week=weekday, hour=int(send_time.split(":")[0]), minute=int(send_time.split(":")[1]))
        scheduler.start()

if env.bool("SCHEDULE"):
    thread = Thread(target=schedule_weekly_message)
    thread.start()

bot.polling()
