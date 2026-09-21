import os
from cryptography.fernet import Fernet
import sqlalchemy.types as types

# Resolve paths relative to the project root (one level up from app/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_PATH = os.path.join(BASE_DIR, "lodestar.key")

def get_key() -> bytes:
    """Load the Fernet key from lodestar.key, or generate one if it doesn't exist."""
    if not os.path.exists(KEY_PATH):
        key = Fernet.generate_key()
        with open(KEY_PATH, "wb") as f:
            f.write(key)
        return key
    else:
        with open(KEY_PATH, "rb") as f:
            return f.read().strip()

# Initialize the Fernet instance for SQLAlchemy types
_fernet = Fernet(get_key())

class EncryptedString(types.TypeDecorator):
    """A String type that encrypts data when saving and decrypts when reading."""
    impl = types.String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # value should be a string; encode to bytes, encrypt, then decode to string for DB storage
        encrypted_bytes = _fernet.encrypt(value.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # SQLite returns string; encode to bytes, decrypt, decode to string
        try:
            decrypted_bytes = _fernet.decrypt(value.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except Exception:
            # If decryption fails (e.g., data was saved unencrypted before migration), return as is or handle it
            # This allows graceful failure if the user hasn't run the migration script yet
            return value


class EncryptedText(types.TypeDecorator):
    """A Text type that encrypts data when saving and decrypts when reading."""
    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        encrypted_bytes = _fernet.encrypt(value.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            decrypted_bytes = _fernet.decrypt(value.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except Exception:
            return value
