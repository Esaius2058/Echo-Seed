import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from ..security.token_manager import TokenManager
from cryptography.fernet import Fernet

key = Fernet.generate_key()
tm = TokenManager(key)
base_dir = Path(__file__).resolve().parents[2]
env_path = base_dir / ".env"

def test_load_and_save_token():
    dummy_data = {"access_token": "abc123"}

    tm.update_token(dummy_data)
    loaded = tm.get_token()

    assert loaded["access_token"] ==  "abc123"

def test_clear_token():
    tm.clear_token()

    assert os.path.exists(tm.token_file_path) == False
    assert not tm.get_token()

def test_rotate_key():
    token = {"access_token" : "lightierr"}
    tm.save_token(token)

    new_key = Fernet.generate_key()

    encrypted = tm.fernet.encrypt(token["access_token"].encode())

    rotated = tm.rotate_key(new_key, encrypted)
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        secret = "SECRET_KEY"
        for i, line in enumerate(lines):
            if line.startswith(f"{secret}="):
                secret = lines[i]
                break

        assert secret == f"SECRET_KEY={new_key.decode("utf-8")}"
        assert tm.fernet.decrypt(rotated).decode() == token["access_token"]

def test_fail_decrypt_with_wrong_key():
    token = {"access_token": "hol'up"}
    tm.save_token(token)

    tm2 = TokenManager(Fernet.generate_key())
    assert not tm2.load_token()

"""def test_refresh_token():
    old_token = {"access_token": "old_token"}
    tm.save_token(old_token)

    new_token = {"access_token": "new_token"}

    with patch.object(TokenManager, "_perform_refresh", return_value=new_token):
        tm.refresh_token()

    loaded = tm.load_token()

    assert loaded["access_token"] == "new_token"
"""