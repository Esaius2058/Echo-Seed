import json
import logging
import requests
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet, MultiFernet
from pathlib import Path

class TokenManager:
    def __init__(self, encryption_key: bytes):
        base_dir = Path(__file__).resolve().parents[2]
        self.token_file_path = base_dir / "tokens.json.enc"
        self.logger = logging.getLogger(__name__)
        self.fernet = Fernet(encryption_key)
        self.token_data = None
        self.load_token()

    def load_token(self):
        """Loads and decrypts token from file if it exists."""
        if os.path.exists(self.token_file_path):
            with open(self.token_file_path, "rb") as f:
                encrypted_data = f.read()
            try:
                decrypted_data = self.fernet.decrypt(encrypted_data)
                self.token_data = json.loads(decrypted_data.decode())
            except Exception as e:
                print(f"[TokenManager] Failed to decrypt token: {e}")
                self.token_data = None

    def save_token(self, token_data):
        try:
            json_data = json.dumps(token_data).encode()
            encrypted_data = self.fernet.encrypt(json_data)
            with open(self.token_file_path, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"[TokenManager] Failed to save token: {e}")

    def get_token(self):
        self.load_token()
        return self.token_data

    def update_token(self, new_token_data: dict):
        self.token_data = new_token_data
        self.save_token(new_token_data)

    def clear_token(self):
        if os.path.exists(self.token_file_path):
            os.remove(self.token_file_path)
        self.token_data = None

    def rotate_key(self, new_key:bytes = None, encrypted_token: bytes = None) -> bytes:
        if not new_key:
            new_key = Fernet.generate_key()

        old_fernet = self.fernet
        multi_fernet = MultiFernet([Fernet(new_key), old_fernet])

        rotated = None
        if encrypted_token:
            rotated = multi_fernet.rotate(encrypted_token)

        self.fernet = Fernet(new_key)
        self._update_env_file("SECRET_KEY", new_key.decode())

        return rotated

    def _update_env_file(self, new_key:str, new_value:str):
        lines = []
        found = False
        base_dir = Path(__file__).resolve().parents[2]
        env_path = base_dir / ".env"
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if line.startswith(f"{new_key}="):
                    lines[i] = f"{new_key}={new_value}"
                    found = True
                    break

        if not found:
            lines.append(f"{new_key}={new_value}")

        with open(env_path, "w", encoding="utf-8") as f:
            self.logger.info(f"Writing Lines to ENV file...")
            f.writelines(lines)

    def refresh_token(self):
        token_data = self.get_token()
        if not token_data or "refresh_token" not in token_data:
            print("[TokenManager] No refresh_token available.")
            return None

        refresh_token = token_data["refresh_token"]

        try:
            response = requests.post(
                "https://example.com/oauth/refresh",
                json={"refresh_token": refresh_token},
                timeout=10
            )
            if response.status_code == 200:
                new_token_data = response.json()
                self.update_token(new_token_data)
                print("[TokenManager] Token refreshed successfully.")
                return new_token_data
            else:
                print(f"[TokenManager] Refresh failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"[TokenManager] Error refreshing token: {e}")
            return None

if __name__ == "__main__":
    load_dotenv()
    key = os.getenv("SECRET_KEY").encode()

    tm = TokenManager(key)
    tm.update_token({"access_token": "12345", "expires_at": "2025-08-14T00:00:00Z"})
    print("Loaded Token:", tm.get_token())