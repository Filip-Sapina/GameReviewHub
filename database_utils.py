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
        username = fake.user_name()
        password = fake.password()
        date_joined = int(datetime.now().timestamp())
        password_hash = sha256(password.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO Users (username, password_hash, date_joined) VALUES (?, ?, ?)",
            (username, password_hash, date_joined)
        )
        print(f"{username}, {password}")

    db.commit()
    cursor.close()
    db.close()
    print(f"{n} fake users added to the database.")

def clear_users():
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute("DELETE FROM Users")
    db.commit()
    cursor.close()
    db.close()
    print("cleared users")


if sys.argv[1].lower() == "generate_users":
    generate_users(int(sys.argv[2]))
if sys.argv[1].lower() == "clear_users":
    clear_users()