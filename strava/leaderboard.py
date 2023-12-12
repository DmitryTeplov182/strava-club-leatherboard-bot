from selenium import webdriver
from selenium.webdriver.common.by import By

import config
from strava.page_utils import StravaPageUtils


class StravaLeaderboard(StravaPageUtils):
    """A class for interacting with the Strava leaderboard of a club."""

    def __init__(self, browser: webdriver):
        super().__init__(browser)
        self.browser = browser

    def get_this_week_or_last_week_leaders(
        self, club_id: int, last_week=True
    ) -> list:
        """Get the leaders of a club for this or last week."""
        self._open_page(f"{config.BASE_URL}/clubs/{str(club_id)}/leaderboard")

        if last_week:
            self._click_last_week_button()

        return self._get_data_leaderboard()

    def _get_data_leaderboard(self) -> list:
        """Get data leaderboard"""

        leaderboard = []
        table = self._wait_element((By.CLASS_NAME, "dense"))
        trows = table.find_elements(By.TAG_NAME, "tr")[1:]

        for trow in trows:
            athlete_url = (
                trow.find_element(By.TAG_NAME, "a")
                .get_attribute("href")
                .strip()
            )
            avatar_medium = (
                trow.find_element(By.TAG_NAME, "img")
                .get_attribute("src")
                .strip()
            )
            avatar_large = avatar_medium.replace("medium", "large")

            # Extract text values from 'td' elements and assign them to variables
            (
                rank,
                athlete_name,
                distance,
                activities,
                longest,
                avg_pace,
                elev_gain,
            ) = (td.text for td in trow.find_elements(By.TAG_NAME, "td"))

            athlete_data = {
                "rank": rank,
                "athlete_name": athlete_name,
                "distance": distance,
                "activities": activities,
                "longest": longest,
                "avg_pace": avg_pace,
                "elev_gain": elev_gain,
                "avatar_large": avatar_large,
                "avatar_medium": avatar_medium,
                "link": athlete_url,
            }

            leaderboard.append(athlete_data)

        count_athletes = len(leaderboard)
        config.logger.info(
            "A list of dictionaries with athlete data from the table "
            "has been generated for %s athletes of the club",
            count_athletes,
        )
        return leaderboard

    def _click_last_week_button(self):
        """Click last week button on table"""
        self._wait_element((By.CLASS_NAME, "last-week")).click()
        config.logger.info("Go to last week's leaderboard")
