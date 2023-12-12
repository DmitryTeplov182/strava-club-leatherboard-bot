import logging
import gettext

from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

from babel import Locale
from babel.dates import format_date

from environs import Env

# Read environment variables
env = Env()
env.read_env()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Base URL
BASE_URL = "https://www.strava.com"

# Chrome driver options
option_arguments = [
    "--headless=new",
    "--hide-scrollbars",
    "start-maximized",
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
    "disable-popup-blocking",
]

# Create a scheduler
scheduler = BlockingScheduler(timezone=env.str("TZ"))

# Locale

# We create a locale (language) object for translation
locale = Locale(env.str("LOCALE"))

# Initialize the gettext object to use the current locale
translate = gettext.translation(
    "bot", localedir="locales", languages=[locale.language]
)


def format_and_translate_date(date: datetime) -> dict:
    """Format and translate a date."""

    # Format the date, month, and year using Babel
    formatted_week = format_date(date, format="w", locale=locale)
    formatted_month = format_date(date, format="MMMM", locale=locale)
    formatted_year = format_date(date, format="yyyy", locale=locale)

    # Create a dictionary to hold the variables for substitution
    variables = {
        "week": formatted_week,
        "month": formatted_month,
        "year": formatted_year,
    }

    return variables
