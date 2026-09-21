import os
import sys
import sqlite3

# Resolve paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.encryption import get_key
from cryptography.fernet import Fernet, InvalidToken

def is_encrypted(value: str) -> bool:
    if not value:
        return False
    # Fernet tokens usually start with 'gAAAAA'
    return value.startswith("gAAAAA")

def encrypt_value(fernet, value):
    if not value or is_encrypted(value):
        return value
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")

def migrate_db():
    db_path = os.path.join(BASE_DIR, "data", "lodestar.db")
    if not os.path.exists(db_path):
        print(f"No database found at {db_path}. Nothing to migrate.")
        return

    key = get_key()
    fernet = Fernet(key)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Migrate Cases (notes)
        cursor.execute("SELECT id, notes FROM cases")
        cases = cursor.fetchall()
        for case_id, notes in cases:
            if notes and not is_encrypted(notes):
                cursor.execute("UPDATE cases SET notes = ? WHERE id = ?", (encrypt_value(fernet, notes), case_id))

        # Migrate Findings (value, source_url, notes)
        cursor.execute("SELECT id, value, source_url, notes FROM findings")
        findings = cursor.fetchall()
        for f_id, value, source_url, notes in findings:
            if any(not is_encrypted(v) for v in (value, source_url, notes) if v):
                cursor.execute(
                    "UPDATE findings SET value = ?, source_url = ?, notes = ? WHERE id = ?",
                    (encrypt_value(fernet, value), encrypt_value(fernet, source_url), encrypt_value(fernet, notes), f_id)
                )
                
        # Migrate Images (source_url, exif_json)
        # Note: Depending on earlier phases, 'images' table might not exist or be populated. Use try/except.
        try:
            cursor.execute("SELECT id, source_url, exif_json FROM images")
            images = cursor.fetchall()
            for img_id, source_url, exif_json in images:
                if any(not is_encrypted(v) for v in (source_url, exif_json) if v):
                    cursor.execute(
                        "UPDATE images SET source_url = ?, exif_json = ? WHERE id = ?",
                        (encrypt_value(fernet, source_url), encrypt_value(fernet, exif_json), img_id)
                    )
        except sqlite3.OperationalError:
            pass # Table might not exist

        # Migrate Relationships (person_a, person_b, source_url)
        try:
            cursor.execute("SELECT id, person_a, person_b, source_url FROM relationships")
            rels = cursor.fetchall()
            for rel_id, person_a, person_b, source_url in rels:
                if any(not is_encrypted(v) for v in (person_a, person_b, source_url) if v):
                    cursor.execute(
                        "UPDATE relationships SET person_a = ?, person_b = ?, source_url = ? WHERE id = ?",
                        (encrypt_value(fernet, person_a), encrypt_value(fernet, person_b), encrypt_value(fernet, source_url), rel_id)
                    )
        except sqlite3.OperationalError:
            pass # Table might not exist

        conn.commit()
        print("Migration successful! Sensitive data has been encrypted.")
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
