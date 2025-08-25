import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet, MultiFernet

class TokenManager:
    def __init__(self, encryption_key: bytes):
        base_dir = Path(__file__).resolve().parents[2]
        self.token_file_path = base_dir / "tokens.json.enc"
        self.logger = logging.getLogger("echoseed.token_manager")
        self.fernet = Fernet(encryption_key)
        self.token_data = None
        self.load_token()

    def save_token(self, token_data):
        try:
            json_data = json.dumps(token_data).encode()
            encrypted_data = self.fernet.encrypt(json_data)
            with open(self.token_file_path, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"[TokenManager] Failed to save token: {e}")

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

    def get_token(self):
        if not self.token_data:
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
            self.logger.info(f"[TokenManager]Writing Lines to ENV file...")
            f.writelines(lines)


if __name__ == "__main__":
    load_dotenv()
    key = os.getenv("SECRET_KEY").encode()

    tm = TokenManager(key)
    tm.update_token({"access_token": "12345", "expires_at": "2025-08-14T00:00:00Z"})
    print("Loaded Token:", tm.get_token())