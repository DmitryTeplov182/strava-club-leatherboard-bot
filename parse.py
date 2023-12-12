from __future__ import annotations
import config
from strava.authorization import StravaAuthorization
from strava.browser import BrowserManager
from strava.exceptions import AuthorizationFailureException
from strava.leaderboard import StravaLeaderboard


class StravaLeaderboardRetriever:
    """Retrieves Strava leaderboard data for a given club."""

    def __init__(self, email: str, password: str, club_id: int):
        self.club_id = club_id
        self.browser = BrowserManager().start_browser()
        self.auth = StravaAuthorization(self.browser, email, password)
        self.leaderboard = StravaLeaderboard(self.browser)

    def retrieve_leaderboard_data(
        self, last_week: bool = True
    ) -> list[dict[str, str]] | None:
        """Retrieve leaderboard data for the specified Strava club."""
        try:
            self.auth.authorization()
            leaderboard_data = (
                self.leaderboard.get_this_week_or_last_week_leaders(
                    self.club_id,
                    last_week,
                )
            )
            return leaderboard_data
        except AuthorizationFailureException as auth_error:
            config.logger.error(
                "Strava authorization error: %s", str(auth_error)
            )
        except Exception as e:
            config.logger.error("An error occurred: %s", str(e))
        finally:
            self.browser.quit()
        return None
