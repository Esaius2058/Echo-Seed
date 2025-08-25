import logging
import os
import time

from dotenv import load_dotenv
from config import logger_config
import requests
from echoseed.security.token_manager import TokenManager

class NetworkMonitor:
    logger_config.setup_logger()

    def __init__(self, test_url="https://www.google.com", check_interval=40, refresh_callback=None):
        self.test_url = test_url
        self.check_interval = check_interval
        self.refresh_callback = refresh_callback
        self.last_status = None
        self.logger = logging.getLogger("echoseed.network_monitor")
        self.running = False

    def check_connection(self) -> bool:
        self.logger.info(f"[NetworkMonitor] pinging {self.test_url} to check connection")
        try:
            response = requests.get(self.test_url, timeout=5)
            self.logger.info(f"[NetworkMonitor] ping successful")
            return response.status_code == 200
        except requests.RequestException as e:
            self.logger.info(f"[NetworkMonitor] Failed to ping {self.test_url}")
            return False

    def log_status(self):
        status_text = "ONLINE" if self.last_status else "OFFLINE"
        self.logger.info(f"[Network Status] {status_text}")

    def handle_status_change(self, is_online):
        if not self.last_status:
            self.last_status = is_online
            return

        if is_online != self.last_status:
            if is_online == True & self.refresh_callback:
                self.logger.info("[NetworkMonitor] Network restored. Triggering token refresh...")
                self.refresh_callback()
            self.last_status = is_online

    def run(self):
        self.logger.info("[NetworkMonitor] Starting network monitoring...")
        self.logger.info("[NetworkMonitor] Ctrl+C to stop")
        self.running = True
        try:
            while self.running:
                is_online = self.check_connection()
                self.log_status()
                self.handle_status_change(is_online)
                self.log_status()
                time.sleep(self.check_interval)
                break
        except KeyboardInterrupt:
            self.logger.info("[NetworkMonitor] Stopping network monitoring (Ctrl+C detected)!")
        finally:
            self.running = False
            self.logger.info("[NetworkMonitor] Network monitor stopped.")

    def stop(self):
        self.running = False

if __name__ == "__main__":
    load_dotenv()
    encryption_key = os.getenv("SECRET_KEY").encode()
    tm = TokenManager(encryption_key)
    nm = NetworkMonitor()

    nm.run()