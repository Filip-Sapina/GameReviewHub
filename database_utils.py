"""
Toolset for testing/debugging database with fake data
"""

import sqlite3
import sys
from datetime import datetime
from hashlib import sha256
from faker import Faker


DATABASE = "database.db"
fake = Faker()


def generate_users(n):
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    for _ in range(n):
        username = fake.pystr(min_chars=5, max_chars=20)
        password = fake.password()
        date_joined = int(datetime.now().timestamp())

        password_hash = sha256(password.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO Users (username, password_hash, date_joined) VALUES (?, ?, ?)",
            (username, password_hash, date_joined),
        )
        print(f"{username}, {password}")

    db.commit()
    cursor.close()
    db.close()
    print(f"{n} fake users added to the database.")


def create_user(username: str, password: str):
    """
    Creates a user in the Users database. better for a user which you want to know the password to.

    Args:
        username (str): Username of the user that will be made
        password (str): Password of user that will be hashed and stored

    Returns:
        None

    Raises:
        sqlite3.IntegrityError:
            error raised if username is not unique
    """
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    password_hash = sha256(password.encode()).hexdigest()
    date_joined = datetime.now().timestamp()
    cursor.execute(
        "INSERT INTO Users (username, password_hash, date_joined) VALUES (?, ?, ?)",
        (username, password_hash, date_joined),
    )
    print("added user")
    db.commit()
    cursor.close()
    db.close()


def clear_users():
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("DELETE FROM Users")
    cursor.execute("UPDATE sqlite_sequence SET seq=0 WHERE name='Users'")
    db.commit()
    cursor.close()
    db.close()
    print("cleared users")


if sys.argv[1].lower() == "generate_users":
    generate_users(int(sys.argv[2]))
if sys.argv[1].lower() == "create_user":
    create_user(sys.argv[2], sys.argv[3])
if sys.argv[1].lower() == "clear_users":
    clear_users()
