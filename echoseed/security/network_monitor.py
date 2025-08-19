import logging
import os
from time import sleep
from dotenv import load_dotenv
from config import logger_config
import requests
from echoseed.security.token_manager import TokenManager

class NetworkMonitor:
    logger_config.setup_logger()

    def __init__(self, test_url="https://www.google.com", check_interval=60, refresh_callback=None):
        self.test_url = test_url
        self.check_interval = check_interval
        self.refresh_callback = refresh_callback
        self.last_status = None
        self.logger = logging.getLogger(__name__)
        self.running = False

    def check_connection(self) -> bool:
        try:
            response = requests.get(self.test_url, timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            self.logger.info(f"Failed to ping {self.test_url}")
            return False

    def log_status(self):
        is_online = self.check_connection()
        status_text = "ONLINE" if is_online else "OFFLINE"
        self.logger.info(status_text)

    def handle_status_change(self, is_online):
        if not self.last_status:
            self.last_status = is_online
            return

        if is_online != self.last_status:
            self.logger.info(is_online)

            if is_online == True & self.refresh_callback:
                self.logger.info("Network restored. Triggering token refresh...")
                self.refresh_callback()

            self.last_status = is_online

    def run(self):
        self.logger.info("Starting network monitoring...")
        self.running = True
        try:
            while self.running:
                is_online = self.check_connection()
                self.handle_status_change(is_online)
                sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("Stopping network monitoring (Ctrl+C detected)!")
        finally:
            self.running = False
            self.logger.info("Network monitor stopped.")

    def stop(self):
        self.running = False

if __name__ == "__main__":
    load_dotenv()
    encryption_key = os.getenv("SECRET_KEY").encode()
    tm = TokenManager(encryption_key)
    nm = NetworkMonitor(refresh_callback=tm.refresh_token)

    nm.run()