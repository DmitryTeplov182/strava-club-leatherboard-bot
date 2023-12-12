import config
import telebot
from telebot import types
import json

def parse_value(value):
    try:
        if value == '--':
            return 0

        number = ''.join(filter(lambda x: x.isdigit(), value.replace(' m', '').replace(',', '')))
        return float(number)
    except Exception as e:
        print(f"Error in parse_value: {e}")
        raise


def get_top_athletes(filename, metric):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            athletes = json.load(file)

        athletes.sort(key=lambda x: parse_value(x[metric]), reverse=True)
        return athletes[:5]
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
            name = f"[{athlete['athlete_name']}]({athlete['link']})"
            value = athlete[metric]
            rank_emoji = emoji[index - 1] if index <= 5 else str(index)
            message += f"{rank_emoji} {name}: {value}\n"
        return message
    except Exception as e:
        print(f"Error in format_message: {e}")
        raise

def format_combined_message(filename):
    try:
        message = "*Previous Week:*\n\n"
        club_id = config.env.str("CLUB_ID")
        for metric in ['distance', 'elev_gain', 'longest']:
            top_athletes = get_top_athletes(filename, metric)
            message += format_message(top_athletes, metric) + "\n"
        message += f"[Strava Club Link](https://www.strava.com/clubs/{club_id})"
        return message
    except Exception as e:
        print(f"Error in format_combined_message: {e}")
        raise

bot_token = config.env.str("BOT_TOKEN")
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
        club_id = config.env.str("CLUB_ID")
        filename = f'./jsons/{club_id}.json'
        response_message = format_combined_message(filename)
        bot.send_message(message.chat.id, response_message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        print(f"Error in send_week_top: {e}")
        raise

@bot.inline_handler(lambda query: True)
def inline_query(query):
    try:
        club_id = config.env.str("CLUB_ID")
        filename = f'./jsons/{club_id}.json'
        results = [types.InlineQueryResultArticle(
            id='1',
            title="Top 5 Club Members",
            description="Click to see the top 5 club members by various metrics",
            input_message_content=types.InputTextMessageContent(
                format_combined_message(filename),
                parse_mode='Markdown',
                disable_web_page_preview=True  
            )
        )]
        bot.answer_inline_query(query.id, results)
    except Exception as e:
        print(f"Error in inline_query: {e}")
        raise

bot.polling()
