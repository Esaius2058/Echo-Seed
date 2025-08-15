import json
from dotenv import load_dotenv
import logging
import os
from cryptography.fernet import Fernet
from pathlib import Path

class TokenManager:
    def __init__(self, encryption_key: bytes):
        base_dir = Path(__file__).resolve().parents[2]
        self.token_file_path = base_dir / "tokens.json.enc"
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

if __name__ == "__main__":
    load_dotenv()
    key = os.getenv("SECRET_KEY").encode()

    tm = TokenManager(key)
    tm.update_token({"access_token": "12345", "expires_at": "2025-08-14T00:00:00Z"})
    print("Loaded Token:", tm.get_token())