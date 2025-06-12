"""
Main Application Program, starts flask site.
"""

import sqlite3
from datetime import datetime
from hashlib import sha256

from flask import Flask, g, redirect, url_for, render_template, request, flash, session

app = Flask(__name__)

app.config["SECRET_KEY"] = "AVerySecretKeyThatNooneKnowsAbout"

DATABASE = "database.db"


def make_dicts(cursor, row):
    """row factory for database to turn tuples into dicts"""
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))

def to_hash(password: str):
    return sha256(password.encode()).hexdigest()


def get_database():
    """returns a database connection"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = make_dicts
    return g.db


class Game(object):
    """
    Represents a video game with relevant metadata, same as columns in Game table.

    Attributes:
        title (str): The title of the game.
        description (str): A brief description of the game.
        release_date (int): The release year of the game.
        developer (str): The developer or development studio of the game.
        game_tags (list): A list of tags or genres describing the game.
        platforms (list): A list of platforms on which the game is available.
        publisher (str): The publisher of the game. Defaults to the developer if not provided.
    """
    def __init__(
        self,
        title: str,
        description: str,
        release_date: int,
        developer: str,
        game_tags: list,
        platforms: list,
        publisher: str = None,
    ) -> None:
        self.title = title
        self.description = description
        self.release_date = release_date
        self.developer = developer
        self.game_tags = game_tags
        self.platforms = platforms

        if publisher:
            self.publisher = publisher
        else:
            self.publisher = self.developer

class User(object):
    """
    Represents a user with relevant metadata, same as columns in Users table.

    Attributes:
        user_id (int): Id of user within database's Users table
        username (str): Name of user.
        password_hash (str): Hashed password using sha256.
        date_joined (int): unix timestamp of when user joined
        data (dict): dict containing all variables above, overwrites if provided.
    """
    def __init__(self, user_id = None, username = None, password_hash = None, date_joined = None, data: dict = None) -> None:
        if data:
            self.user_id = data["user_id"]
            self.username = data["username"]
            self.password_hash = data["password_hash"]
            self.date_joined = data["date_joined"]
        else:
            self.user_id = user_id
            self.username = username
            self.password_hash = password_hash
            self.date_joined = date_joined


def get_user_by_id(user_id: int):
    """
    Returns user data from database using user_id

    Args:
        user_id (int): The ID of the user to retrieve.

    Returns:
        user (User): object containing each column of found row in database.
    Raises:
        TypeError: If user_id is not an integer.
    """

    db = get_database()
    db.row_factory = make_dicts
    cursor = db.cursor()
    query = "SELECT * FROM Users WHERE user_id = ?"
    cursor.execute(query, (user_id,))
    user = User(data=cursor.fetchone())
    db.commit()
    if user:
        user.date_joined = datetime.fromtimestamp(user.date_joined)
    return user


def get_user_by_username(username: str):
    """
    Returns user data from database using user_id

    Args:
        username (str): The name of the user to retrieve.

    Returns:
        dict: A dictionary containing the user's details, including the
            'date_joined' field converted to a datetime object.

    Raises:
        TypeError: If username is not an string.
    """

    db = get_database()
    db.row_factory = make_dicts
    cursor = db.cursor()
    query = "SELECT * FROM Users WHERE username = ?"
    cursor.execute(query, (username,))
    user = User(data=cursor.fetchone())
    db.commit()
    if user:
        user.date_joined = datetime.fromtimestamp(user.date_joined)
    else:
        return None

    return user


def add_user(username: str, password: str):
    """
    Add a new user to the database with hashed password and current time as join date.

    Args:
        username (str): Username for new user
        password (str): the non-hashed password for hashing and storing

    Returns:
        None
    """
    date_joined = datetime.now().timestamp()
    password_hash = to_hash(password)

    db = get_database()
    db.row_factory = make_dicts
    cursor = db.cursor()
    insert = "INSERT INTO Users (username, password_hash, date_joined) VALUES (?,?,?)"
    cursor.execute(insert, (username, password_hash, date_joined))
    db.commit()


def delete_user(user_id: int):
    """
    Removes a user from Users Table by user_id

    Args:
        user_id (int): The ID of the user to delete.

    Returns:
        None

    """
    db = get_database()
    db.row_factory = make_dicts
    cursor = db.cursor()
    delete = "DELETE FROM Users WHERE user_id = ?"
    cursor.execute(delete, user_id)


def update_user(user_id: int, username: str = None, password: str = None):
    """
    Updates an existing user's username and/or password in the database

    Args:
        user_id (int): Id of User to update.
        username (str): New username for user.
        password (str): New un-hashed password to be hashed and stored

    Returns:
        None

    Raises:
        ValueError: If neither username nor password is provided
    """

    if username is None and password is None:
        raise ValueError(
            "update_user() requires either username or password, neither were provided"
        )

    db = get_database()
    db.row_factory = make_dicts
    cursor = db.cursor()

    password_hash = to_hash(password)

    if username and not password:
        update = "UPDATE Users SET username = ? WHERE user_id = ?"
        cursor.execute(update, (username, user_id))
    elif not username and password:
        update = "UPDATE Users SET password_hash = ? WHERE user_id = ?"
        cursor.execute(update, (password_hash, user_id))
    else:
        update = "UPDATE Users SET username = ?, password_hash = ?  WHERE user_id = ?"
        cursor.execute(update, (username, password_hash, user_id))

    db.commit()


@app.teardown_appcontext
def close_database_connection(exception):
    """closes database when app has been closed"""
    db = g.pop("db", None)
    if db is not None:
        db.close()
    if exception is not None:
        print("ERROR RAISED ON CLOSING APP")


@app.route("/home")
def home():
    if not "user_id" in session.keys():
        session["user_id"] = None
    if session["user_id"]:
        user = get_user_by_id(session["user_id"])
    else:
        user = {
            "user_id": "N/A",
            "username": "NOT LOGGED IN",
            "password_hash": "NOT LOGGED IN",
            "date_joined": "N/A",
        }
    return render_template("home.html", user=user)


@app.route("/login", methods=["GET", "POST"])
def login_page():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = get_user_by_username(username)
        if user:
            password_hash = to_hash(password)
            if password_hash == user.password_hash:
                session["user_id"] = user.user_id
                flash("Login Accepted")
                return redirect(url_for("home"))
            else:
                flash("Password incorrect")
        else:
            flash("USER NOT FOUND")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session["user_id"] = None
    return redirect(url_for("home"))


@app.route("/")
def index():
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
