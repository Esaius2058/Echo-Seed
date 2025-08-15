import os
from cryptography.fernet import Fernet, MultiFernet
from dotenv import load_dotenv
import datetime
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY")
        if not self.secret_key:
            logger.error("SECRET_KEY not set in environment variables")
            raise RuntimeError("SECRET_KEY not set in environment variables")
        self.fernet = Fernet(self.secret_key)

    def encrypt_token(self, token: str) -> bytes:
        encrypted_token = self.fernet.encrypt(token.encode())
        return encrypted_token

    def decrypt_token(self, token_bytes: bytes) -> str:
        decrypted_token = self.fernet.decrypt(token_bytes)
        return decrypted_token.decode()

    def rotate_key(self, stored_tokens: list[bytes], new_key: str = None):
        if new_key is None:
            new_key = Fernet.generate_key()

        multi_fernet = MultiFernet([Fernet(new_key), self.fernet])
        rotated_tokens = [multi_fernet.rotate(token) for token in stored_tokens]
        self.secret_key = new_key
        self.fernet = Fernet(new_key)

        self._update_env_file("SECRET_KEY", new_key.decode())

        logger.info("Key rotated successfully. .env updated.")
        return new_key, rotated_tokens

    def _update_env_file(self, key: str, value: str):
        env_path = ".env"
        lines = []
        found = False

        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    found = True
                    break

            if not found:
                lines.append(f"{key}={value}\n")

            with open(env_path, "w") as f:
                f.writelines(lines)