from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.common import TimeoutException, NoSuchElementException

import config


class StravaPageUtils:
    """
    A base class providing common methods for interacting with the Strava
    web application.
    """

    def __init__(self, browser: webdriver):
        self.browser = browser

    def _check_element(
        self, by_element: tuple, timeout: int = 0, until_not: bool = False
    ) -> bool:
        """Check if an element is present on the page."""
        wait = WebDriverWait(self.browser, timeout)
        try:
            if until_not:
                wait.until_not(ec.visibility_of_element_located(by_element))
            else:
                wait.until(ec.visibility_of_element_located(by_element))
        except (TimeoutException, NoSuchElementException):
            return False
        return True

    def _wait_element(
        self, by_element: tuple, timeout: int = 15
    ) -> WebElement:
        """Wait for the element"""
        wait = WebDriverWait(self.browser, timeout)
        try:
            element = wait.until(ec.visibility_of_element_located(by_element))
            return element
        except TimeoutException as e:
            raise TimeoutException("Not found element") from e

    def _open_page(self, url: str):
        """Open the specified page URL in the browser."""
        self.browser.get(url)
        config.logger.info("Open page URL: %s", self.browser.current_url)
