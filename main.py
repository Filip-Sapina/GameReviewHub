"""
Main Application Program, starts flask site.
"""

import sqlite3
from collections import namedtuple
from datetime import datetime
from hashlib import sha256
from faker import Faker
from flask import Flask, g, redirect, url_for, render_template, request, flash, session

app = Flask(__name__)

app.config["SECRET_KEY"] = "AVerySecretKeyThatNooneKnowsAbout"

# Generic Database Logic

DATABASE = "database.db"

def make_dicts(cursor, row) -> dict:
    """row factory for database to turn tuples into dicts"""
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))

def get_database():
    """returns a database connection and cursor object of connection"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = make_dicts

    cursor = g.db.cursor()
    return g.db, cursor


#User Logic

def to_hash(password: str) -> str:
    """
    Hashes a password and returns hex string

    Args:
        password (str): password for hashing
    
    Returns:
        password_hash (str): hex string of password for better security
    """
    return sha256(password.encode()).hexdigest()

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

    def __init__(
        self,
        user_id=None,
        username=None,
        password_hash=None,
        date_joined=None,
        data: dict = None,
    ) -> None:
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

def get_user_by_id(user_id: int) -> User:
    """
    Returns user data from database using user_id

    Args:
        user_id (int): The ID of the user to retrieve.

    Returns:
        user (User): object containing each column of found row in database.
    Raises:
        TypeError: If user_id is not an integer.
    """

    db, cursor = get_database()
    query = "SELECT * FROM Users WHERE user_id = ?"
    cursor.execute(query, (user_id,))
    data = cursor.fetchone()
    if data:
        data["date_joined"] = datetime.fromtimestamp(data["date_joined"])
    else:
        return None
    user = User(data=data)
    db.commit()
    return user

def get_user_by_username(username: str) -> User:
    """
    Returns user data from database using username

    Args:
        username (str): The name of the user to retrieve.

    Returns:
        user (User): object containing each column of found row in database.

    Raises:
        TypeError: If username is not an string.
    """

    db, cursor = get_database()
    query = "SELECT * FROM Users WHERE username = ?"
    cursor.execute(query, (username,))
    user = User(data=cursor.fetchone())
    data = cursor.fetchone()
    if data:
        data["date_joined"] = datetime.fromtimestamp(data["date_joined"])
    else:
        return None
    user = User(data=data)
    db.commit()
    return user

def add_user(username: str, password: str) -> None:
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

    db, cursor = get_database()
    insert = "INSERT INTO Users (username, password_hash, date_joined) VALUES (?,?,?)"
    cursor.execute(insert, (username, password_hash, date_joined))
    db.commit()

def delete_user(user_id: int) -> None:
    """
    Removes a user from Users Table by user_id

    Args:
        user_id (int): The ID of the user to delete.

    Returns:
        None

    """
    db, cursor = get_database()
    delete = "DELETE FROM Users WHERE user_id = ?"
    cursor.execute(delete, user_id)
    db.commit()

def update_user(user_id: int, username: str = None, password: str = None) -> None:
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

    db, cursor = get_database()

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


#Game Tag Logic

GameTag = namedtuple("GameTag", ["id", "name"])
"""
Representation of a row of GameTags table in database.
"""

def get_tags_by_game_name(game_name: str) -> list[GameTag]:
    """
    gets a list of game tags associated with the game

    Args:
        game_name (str): title of game to find tags of
    Returns:
        tags: (list[GameTag]): A list of GameTag namedTuples with id and name
    Raises:
        TypeError: if game_name is not a string.
    """
    db, cursor = get_database()

    query = "SELECT game_tag_id FROM Games g JOIN GameTagAssignment gt ON g.game_id = gt.game_id WHERE g.title = ?"
    cursor.execute(query, (game_name,))
    tag_ids = cursor.fetchall()

    tags = []
    for tag_dict in tag_ids:
        tag = get_game_tag_by_id(tag_dict["game_tag_id"])
        tags.append(tag)
    db.commit()
    return tags

def get_game_tag_by_name(tag_name: str) -> GameTag:
    """
    Returns game tag row from database using name.

    Args:
        tag_name (str): The name of the game tag to retrieve.

    Returns:
        GameTag (NameTuple): a tuple with id and name.

    Raises:
        TypeError: If tag_name is not an string.
    """
    db, cursor = get_database()
    query = "SELECT * FROM GameTags WHERE game_tag_name = ?"
    cursor.execute(query, (tag_name,))
    game_tag = cursor.fetchone()
    db.commit()
    return GameTag(game_tag["game_tag_id"], game_tag["game_tag_name"])

def get_game_tag_by_id(tag_id: int) -> GameTag:
    """
    Returns game tag row from database using id.

    Args:
        id (int): The id of the game tag to retrieve.

    Returns:
        GameTag (NameTuple): a tuple with name and id.

    Raises:
        TypeError: If tag_id is not an integer.
    """
    db, cursor = get_database()
    query = "SELECT * FROM GameTags WHERE game_tag_id = ?"
    cursor.execute(query, (tag_id,))
    game_tag = cursor.fetchone()
    db.commit()
    return GameTag(game_tag["game_tag_id"], game_tag["game_tag_name"])


#Platform Logic

Platform = namedtuple("Platform", ["id", "name"])
"""
Representation of a row of Platforms table in database.
"""

def get_platforms_by_game_name(game_name: str) -> list[Platform]:
    """
    gets a list of platforms that a game is playable on.

    Args:
        game_name (str): title of game to find platforms for
    Returns:
        platforms: (list[Platform]): A list of Platform namedTuples with id and name
    Raises:
        TypeError: if game_name is not a string.
    """
    db, cursor = get_database()

    query = "SELECT platform_id FROM Games g JOIN PlatformAssignment p ON g.game_id = p.game_id WHERE g.title = ?"
    cursor.execute(query, (game_name,))
    platform_ids = cursor.fetchall()

    platforms = []
    for platform_dict in platform_ids:
        tag = get_game_tag_by_id(platform_dict["game_tag_id"])
        platforms.append(tag)
    db.commit()
    return platforms

def get_platform_by_name(platform_name: str) -> Platform:
    """
    Returns platform row from database using name.

    Args:
        platform_name (str): The name of the game tag to retrieve.

    Returns:
        GameTag (NameTuple): a tuple with id and name.

    Raises:
        TypeError: If platform_name is not an string.
    """
    db, cursor = get_database()
    query = "SELECT * FROM Platforms WHERE platform_name = ?"
    cursor.execute(query, platform_name)
    platform = cursor.fetchone()
    db.commit()
    return Platform(platform["platform_id"], platform["platform_name"])


#Game Logic

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
        data (Dict): Optional instead of other values, constructors still requires game_tags and platforms alongside this.
    """

    def __init__(
        self,
        platforms: list,
        game_tags: list,
        title: str = None,
        description: str = None,
        release_date: int = None,
        developer: str = None,
        publisher: str = None,
        image_link: str = None,
        game_id: int = None,
        data: dict = None,
    ) -> None:
        if data:
            self.title = data["title"]
            self.description = data["description"]
            self.release_date = data["release_date"]
            self.developer = data["developer"]
            self.image_link = data["image_link"]
            self.id = data["game_id"]

            if "publisher" in data:
                self.publisher = data["publisher"]
            else:
                self.publisher = self.developer
        else:
            self.title = title
            self.description = description
            self.release_date = release_date
            self.developer = developer

            self.image_link = image_link
            self.id = game_id

            if publisher:
                self.publisher = publisher
            else:
                self.publisher = self.developer

        self.game_tags = game_tags
        self.platforms = platforms

def get_game_by_id(game_id: int) -> Game:
    """
    Returns Game object from database using game_id

    Args:
        game_id (int): The ID of the game to retrieve.

    Returns:
        game (Game): object containing each column of found row in database.
    Raises:
        TypeError: If game_id is not an integer.
    """

    db, cursor = get_database()
    query = "SELECT * FROM Games WHERE game_id = ?"
    cursor.execute(query, (game_id,))
    data = cursor.fetchone()
    tags = get_tags_by_game_name(data["title"])
    platforms = get_platforms_by_game_name(data["title"])
    game = Game(platforms, tags, data=data)
    db.commit()
    if game:
        game.release_date = datetime.fromtimestamp(game.release_date)

    return game

def get_game_by_name(game_name: str) -> Game:
    """
    Returns Game object from database using game_name

    Args:
        game_name (str): The Name of the game to retrieve.

    Returns:
        game (Game): object containing each column of found row in database.
    Raises:
        TypeError: If game_name is not a string.
    """

    db, cursor = get_database()
    query = "SELECT * FROM Games WHERE title = ?"
    cursor.execute(query, (game_name,))
    data = cursor.fetchone()
    tags = get_tags_by_game_name(data["title"])
    platforms = get_platforms_by_game_name(data["title"])
    game = Game(platforms, tags, data=data)
    db.commit()
    if game:
        game.release_date = datetime.fromtimestamp(game.release_date)
    return game

def add_game(game: Game) -> None:
    """
    Add a new game to the database and its associated platforms and game_tags.

    Args:
        game (Game): game object that contains all relevant information for adding a new game

    Returns:
        None
    """
    # NOT FUNCTIONAL
    db, cursor = get_database()

    game_insert = "INSERT INTO Games (title, description, release_date, developer, publisher, image_link) VALUES (?,?,?,?,?,?)"
    cursor.execute(
        game_insert,
        (
            game.title,
            game.description,
            game.release_date,
            game.developer,
            game.publisher,
            game.image_link,
        ),
    )

    db.commit()

def link_game_tag(game: Game, game_tag: GameTag) -> None:
    db, cursor = get_database()

    cursor.execute("SELECT * FROM GameTags WHERE game_tag_id = ?", (game_tag.id,))
    if not cursor.fetchone():
        raise KeyError("game_tag.id doesn't exist in the database.")

    insert = "INSERT INTO GameTagAssignment (game_id, game_tag_id) VALUES (?,?)"
    cursor.execute(insert, (game.id, game_tag.id))

    db.commit()
    print("finished")


#Review Logic

#Web App Logic
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
    if not session["user_id"] == None:
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

# Admin Tools


fake = Faker()

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

@app.route("/generate_users", methods=["GET", "POST"])
def generate_user():
    if request.method == "POST":
        if request.form["user_count"].strip().isdigit():
            user_count = int(request.form["user_count"])

            db, cursor = get_database()
            
            for _ in range(user_count):
                username = fake.pystr(min_chars=5, max_chars=20)
                password = fake.password()
                date_joined = int(datetime.now().timestamp())

                password_hash = sha256(password.encode()).hexdigest()
                cursor.execute(
                "INSERT INTO Users (username, password_hash, date_joined) VALUES (?, ?, ?)",
                (username, password_hash, date_joined),
            )
            db.commit()
            flash(f"Successfully added {user_count} users.")
        else:
            flash("USER COUNT MUST BE INTERGER ONLY")
    return redirect(url_for("admin_page"))

@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        add_user(username, password)
    return redirect(url_for("admin_page"))
            

@app.route("/link_tag", methods=["GET", "POST"])    
def link_tag():
    if request.method == "POST":
        game_name = request.form["game_name"]
        tag_name = request.form["tag_name"]

        game = get_game_by_name(game_name)
        tag = get_game_tag_by_name(tag_name)

        link_game_tag(game, tag)
    print(request.method)
    return redirect(url_for("admin_page"))


if __name__ == "__main__":
    app.run(debug=True)
