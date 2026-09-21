import os
import sys

# Resolve paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.encryption import get_key
from cryptography.fernet import Fernet

def restore_db():
    enc_path = os.path.join(BASE_DIR, "data", "lodestar.db.enc")
    restore_path = os.path.join(BASE_DIR, "data", "lodestar_restored.db")

    if not os.path.exists(enc_path):
        print(f"Error: {enc_path} does not exist. No backup to restore.")
        sys.exit(1)

    key = get_key()
    fernet = Fernet(key)

    with open(enc_path, "rb") as f:
        encrypted_data = f.read()

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except Exception as e:
        print(f"Failed to decrypt backup: {e}")
        print("Ensure you are using the correct lodestar.key.")
        sys.exit(1)

    with open(restore_path, "wb") as f:
        f.write(decrypted_data)

    print(f"Restore successful! Decrypted database saved to: {restore_path}")
    print("To use it, rename it to lodestar.db (ensure the server is stopped first).")

if __name__ == "__main__":
    restore_db()
