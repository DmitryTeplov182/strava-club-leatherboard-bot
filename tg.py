import os
import telebot
from telebot import types
import json
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import time
from threading import Thread
from environs import Env
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from cachetools import TTLCache, cached
from selenium.common.exceptions import TimeoutException

# Load environment variables
env = Env()
env.read_env()

# Cache configuration for top athletes data
cache = TTLCache(maxsize=100, ttl=5 * 60 * 60)  # 5 hours

# Function to set up Selenium WebDriver with logging enabled
def selenium_webdriver():
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless=new')  # Run in headless mode
    options.add_argument('--disable-gpu')  # Disable GPU acceleration (optional)
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})  # Enable browser logging
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',  # Default Selenium port
        options=options
    )
    return driver

# Function to authenticate with Strava and retrieve cookies
def strava_authentication(strava_login, strava_password):
    driver = selenium_webdriver()
    driver.get('https://www.strava.com/login')

    try:
        # Explicitly wait for login elements to be present
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, 'email'))
        )
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, 'password'))
        )

        # Enter credentials
        driver.find_element(By.ID, 'email').send_keys(strava_login)
        driver.find_element(By.ID, 'password').send_keys(strava_password)

        # Handle cookie banner if present
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-deny-cookie-banner'))
            ).click()
        except TimeoutException:
            pass  # Cookie banner might not be present, so continue

        # Click the login button
        driver.find_element(By.ID, 'login-button').click()  

        # Wait for login to complete
        WebDriverWait(driver, 60).until(
            lambda d: d.current_url != 'https://www.strava.com/login'
        )

        # Get and print cookies
        all_cookies = driver.get_cookies()
        print("Strava Cookies:")
        for cookie in all_cookies:
            print(cookie)

        # Store the cookies (choose a method: file, database, etc.)
        with open("/tmp/strava_cookies.json", "w") as f:
            json.dump(all_cookies, f)

    except TimeoutException as e:
        print(f"TimeoutException: {e}")
        print("Failed to load elements or login page in time.")
        # Capture and print browser logs
        for entry in driver.get_log('browser'):
            print(f"{entry['level']}: {entry['message']}")
    finally:
        driver.quit()

# Function to load cookies from a file
def load_cookies(filename):
    with open(filename, "r") as f:
        cookies = json.load(f)
    return cookies

# Function to add cookies to a requests session
def add_cookies_to_session(session, cookies):
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

# Function to get top athletes from Strava, cached for 5 hours
@cached(cache)
def get_top_athletes(url, metric):
    try:
        session = requests.Session()
        cookies = load_cookies("/tmp/strava_cookies.json")
        add_cookies_to_session(session, cookies)
        
        headers = {
            'accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
            'x-requested-with': 'XMLHttpRequest'
        }
        response = session.get(url, headers=headers)
        response.raise_for_status()
        athletes = response.json().get('data', [])
        if metric == 'longest':
            for athlete in athletes:
                athlete['longest'] = athlete.get('best_activities_distance', 0)
        return athletes
    except Exception as e:
        print(f"Error in get_top_athletes: {e}")
        raise

# Function to format the message with top athletes
def format_message(top_athletes, metric):
    try:
        emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        full_metric_names = {
            'distance': 'Distance',
            'elev_gain': 'Elevation Gain',
            'longest': 'Longest Ride',
            'velocity': 'Speed'
        }
        message = f"Top 5 by {full_metric_names[metric]}:\n"
        sorted_athletes = sorted(top_athletes, key=lambda x: x[metric], reverse=True)[:5]
        for index, athlete in enumerate(sorted_athletes, start=1):
            name = f"[{athlete['athlete_firstname']} {athlete['athlete_lastname']}]({athlete_profile_url(athlete['athlete_id'])})"
            if metric == 'distance' or metric == 'longest':
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
        metrics = {
            'distance': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=distance',
            'elev_gain': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=elev_gain',
            'longest': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=best_activities_distance',
            'velocity': f'https://www.strava.com/clubs/{club_id}/leaderboard?week_offset=1&per_page=5&sort_by=velocity'
        }
        for metric, url in metrics.items():
            top_athletes = get_top_athletes(url, metric)
            message += format_message(top_athletes, metric) + "\n"
        message += f"[Strava Club Link](https://www.strava.com/clubs/{club_id}) | [Donate To Author](https://telegra.ph/Donaty-na-server-10-21)"
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

# Function to update cookies periodically
def update_cookies():
    strava_login = env.str("STRAVA_LOGIN")
    strava_password = env.str("STRAVA_PASSWORD")
    strava_authentication(strava_login, strava_password)

# Function to schedule cookie updates
def schedule_cookie_updates():
    scheduler = BackgroundScheduler()
    interval = int(env.str("COOKIE_UPDATE_INTERVAL", default="3600"))  # Update every 3600 seconds (1 hour) by default
    scheduler.add_job(update_cookies, 'interval', seconds=interval)
    scheduler.start()

# Start the cookie update scheduler
update_cookies()
schedule_cookie_updates()

# Start polling for Telegram bot messages
bot.polling()
