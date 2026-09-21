import os
import sys

# Resolve paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.encryption import get_key
from cryptography.fernet import Fernet

def backup_db():
    db_path = os.path.join(BASE_DIR, "data", "lodestar.db")
    enc_path = os.path.join(BASE_DIR, "data", "lodestar.db.enc")

    if not os.path.exists(db_path):
        print(f"Error: {db_path} does not exist.")
        sys.exit(1)

    key = get_key()
    fernet = Fernet(key)

    with open(db_path, "rb") as f:
        data = f.read()

    encrypted_data = fernet.encrypt(data)

    with open(enc_path, "wb") as f:
        f.write(encrypted_data)

    print(f"Backup successful! Encrypted database saved to: {enc_path}")
    print("Keep lodestar.key safe, or this backup will be unrecoverable.")

if __name__ == "__main__":
    backup_db()
