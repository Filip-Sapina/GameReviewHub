"""
Toolset for testing/debugging database with fake data
"""

import sqlite3
import sys
from faker import Faker


DATABASE = "database.db"
fake = Faker()

def create_tag(name: str):
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO GameTags (game_tag_name) VALUES (?)",
        (name,),
    )
    print("added tag")
    db.commit()
    cursor.close()
    db.close()

if sys.argv[1].lower() == "create_tag":
    create_tag(sys.argv[2])
