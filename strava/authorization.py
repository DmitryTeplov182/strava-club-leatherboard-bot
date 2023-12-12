from selenium import webdriver
from selenium.webdriver.common.by import By

import config
from strava.cookie_manager import CookieManager
from strava.exceptions import AuthorizationFailureException
from strava.page_utils import StravaPageUtils


class StravaAuthorization(StravaPageUtils):
    """Handles Strava user authentication."""

    def __init__(self, browser: webdriver, email: str, password: str):
        super().__init__(browser)
        self.email = email
        self.password = password
        self.browser = browser
        self.cookie_manager = CookieManager(email)

    def authorization(self):
        """
        Performs user authentication.

        This method opens the login page, attempts to read cookies, and, in case of failure,
        performs authentication using a username and password.
        """
        self._open_page(f"{config.BASE_URL}/login")
        cookies = self.cookie_manager.read_cookie()

        if cookies is not None and self._check_apply_cookies(cookies):
            config.logger.info("Cookies have been successfully applied.")
        else:
            config.logger.warning(
                "Invalid cookies! Authorization failed. "
                "Authentication will be attempted using a login and password."
            )
            self.cookie_manager.remove_cookie()
            self._login(self.email, self.password)

    def _login(self, username: str, password: str):
        """Sign in to the Strava"""
        self._input_email(username)
        self._input_password(password)
        self._click_submit_login()

        if self._check_alert_msg():
            raise AuthorizationFailureException(
                "The username or password did not match."
            )

        config.logger.info("Authorization successful.")
        self.cookie_manager.save_cookie(self.browser.get_cookies())

    def _check_apply_cookies(self, cookies: list[dict[str, str]]) -> bool:
        """Check if a cookie has been applied"""
        self._add_cookies(cookies)
        self.browser.refresh()
        check = self._check_element(
            (By.CLASS_NAME, "btn-signup"), timeout=1, until_not=True
        )
        return check

    def _check_alert_msg(self) -> bool:
        """Check if the alert"""
        return self._check_element((By.CLASS_NAME, "alert-message"))

    def _add_cookies(self, cookies: list[dict[str, str]]) -> None:
        """Add cookies to the browser."""
        for cookie in cookies:
            self.browser.add_cookie(cookie)

    def _click_submit_login(self):
        """Click Login button submit"""
        self._wait_element((By.ID, "login-button")).click()

    def _input_email(self, email: str):
        """Input email address"""
        field = self._wait_element((By.ID, "email"))
        field.clear()
        field.send_keys(email)

    def _input_password(self, password: str):
        """Input password"""
        field = self._wait_element((By.ID, "password"))
        field.clear()
        field.send_keys(password)
