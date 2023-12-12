import os
import pickle

import config


class CookieManager:
    """CookieManager is a utility class for managing user-specific cookies."""

    def __init__(self, email: str):
        self.email = email
        self.filename = f"{self.email.split('@')[0]}.cookies"
        self.file_path = os.path.join(
            config.BASE_DIR, f"cookies/{self.filename}"
        )

    def save_cookie(self, cookies):
        """Save cookies to a file."""
        with open(self.file_path, "wb") as cookie_file:
            pickle.dump(cookies, cookie_file)
            config.logger.info("Cookie file is saved.")

    def read_cookie(self):
        """Read cookies from a file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "rb") as cookie_file:
                cookies = pickle.load(cookie_file)
                config.logger.info("Cookie file found. Reading...")
                return cookies
        return None

    def remove_cookie(self):
        """Remove cookies."""
        if os.path.exists(self.file_path):
            config.logger.warning("Delete the file with invalid cookies.")
            os.remove(self.file_path)
