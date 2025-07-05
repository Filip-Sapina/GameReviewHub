"""
Main Application Program, starts flask site.
"""

import sqlite3
from collections import namedtuple
from datetime import datetime
from hashlib import sha256
from faker import Faker
from werkzeug import security
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


def levenshtein_distance(a: str, b: str) -> int:
    """
    compares two strings and returns a number based on how many edits it takes to reach each other.
    https://en.wikipedia.org/wiki/Levenshtein_distance#Iterative_with_full_matrix
    """
    a = a.lower()
    b = b.lower()

    # if either string is empty, the other strings length will equal the distance.
    if a == "" or b == "":
        return max(len(a), len(b))
    # if the strings are the same, there is no edit distance.
    if a == b:
        return 0

    m, n = len(a), len(b)

    # creates a matrix where on side is string a and the other is string b
    matrix = []
    for _ in range(m + 1):
        matrix.append([0] * (n + 1))

    # sets first row and column to 1, 2, 3...
    for i in range(m + 1):
        matrix[i][0] = i
    for j in range(n + 1):
        matrix[0][j] = j

    # fills in the rest of the matrix with minimum edit distance
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            # cost to substitue letter
            cost = 0 if a[i - 1] == b[j - 1] else 1
            # fills in cell based on minimum required changes.
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,  # cost to delete
                matrix[i][j - 1] + 1,  # cost to insert
                matrix[i - 1][j - 1] + cost,  # cost to substitute
            )
    return matrix[m][n]


# User Logic


class User(object):
    """
    Represents a user with relevant metadata, same as columns in Users table.

    Attributes:
        username (str): name of the user.
        user_id (int): id of the user in Users table.
        pasword_hash (str): hashed version of user's password
        date_joined (int): unix timestamp format of when user made account.
        data (dict): dict containing all variables.
    """

    def __init__(self, **data):
        self.username = data.get("username")
        self.password_hash = data.get("password_hash")
        self.date_joined = data.get("date_joined")
        self.user_id = data.get("user_id")
        


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
    user = User(**data)
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
    data = cursor.fetchone()
    print(data["username"])
    if data is None:
        print("no user found")
        return None
    user = User(**data)
    print(user.username)
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
    password_hash = security.generate_password_hash(password)

    db, cursor = get_database()
    insert = "INSERT INTO Users (username, password_hash, date_joined) VALUES (?,?,?)"
    cursor.execute(insert, (username, password_hash, date_joined))
    db.commit()


def delete_user_by_id(user_id: int) -> None:
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

    password_hash = security.generate_password_hash(password)

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


# Game Tag Logic

GameTag = namedtuple("GameTag", ["id", "name"])
"""
Representation of a row of GameTags table in database.
"""


def add_game_tag(name: str) -> None:
    """
    Adds a new game tag into the GameTags database

    Args:
        name (str): the name of the game tag

    Returns:
        None
    """
    db, cursor = get_database()
    insert = "INSERT INTO GameTags (game_tag_name) VALUES (?)"
    cursor.execute(insert, (name,))
    db.commit()


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

    query = """
            SELECT game_tag_id FROM Games g
            JOIN GameTagAssignment gt 
            ON g.game_id = gt.game_id WHERE g.title = ?
            """
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


def update_game_tag(new_tag: GameTag):
    """
    effectively changes the name of the gametag with the given id.

    Args:
        new_tag (GameTag): id of current tag and name to update
    Returns:
        None
    """

    db, cursor = get_database()

    update = "UPDATE GameTags SET game_tag_name = ? WHERE game_tag_id = ?"
    cursor.execute(update, (new_tag.name, new_tag.id))
    db.commit()


def delete_game_tag_by_id(tag_id: int):
    """
    Deletes game tag in the GameTags table and removes all connections
    in GameTagAssignment table.

    Args:
        tag_id (int): id of the game_tag that will be deleted
    Returns:
        None
    """
    db, cursor = get_database()
    delete_game_tag = "DELETE FROM GameTags WHERE game_tag_id = ?"
    delete_links = "DELETE FROM GameTagAssignment WHERE game_tag_id = ?"
    cursor.execute(delete_game_tag, tag_id)
    cursor.execute(delete_links, tag_id)
    db.commit()


# Platform Logic

Platform = namedtuple("Platform", ["id", "name"])
"""
Representation of a row of Platforms table in database.
"""


def add_platform(platform_name: str) -> None:
    """
    Adds a new platform row to Platforms table in database.
    Args:
        platform (str): platform's name.
    Returns:
        None
    """

    db, cursor = get_database()
    insert = "INSERT INTO Platforms (platform_name) VALUES (?)"
    cursor.execute(insert, platform_name)
    db.commit()


def delete_platform_by_id(platform_id: int):
    """
    Deletes a platform row in database using id.
    Args:
        platform_id (int): id of platform to delete
    Returns:
        None
    """
    db, cursor = get_database()
    delete = "DELETE FROM Platforms WHERE platform_id = ?"
    cursor.execute(delete, platform_id)
    db.commit()


def update_platform(new_platform: Platform):
    """
    effectively changes the name of the platform with the given id.

    Args:
         (Platform): id of current platform and name to update
    Returns:
        None
    """

    db, cursor = get_database()

    update = "UPDATE Platforms SET platform_name = ? WHERE platform_id = ?"
    cursor.execute(update, (new_platform.name, new_platform.id))
    db.commit()


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

    query = """
            SELECT platform_id FROM Games g 
            JOIN PlatformAssignment p ON 
            g.game_id = p.game_id WHERE g.title = ?
            """
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
        Platform (NameTuple): a tuple with id and name.

    Raises:
        TypeError: If platform_name is not an string.
    """
    db, cursor = get_database()
    query = "SELECT * FROM Platforms WHERE platform_name = ?"
    cursor.execute(query, platform_name)
    platform = cursor.fetchone()
    db.commit()
    return Platform(platform["platform_id"], platform["platform_name"])


def get_platform_by_id(platform_id: int) -> Platform:
    """
    Returns platform row from database using id.

    Args:
        platform_id (str): The id of the game tag to retrieve.

    Returns:
        Platform (NamedTuple): a tuple with id and name.

    """
    db, cursor = get_database()
    query = "SELECT * FROM Platforms WHERE platform_id = ?"
    cursor.execute(query, platform_id)
    data = cursor.fetchone()
    db.commit()
    return Platform(data["platform_id"], data["platform_name"])


# Game Logic


class Game(object):
    """
    Represents a video game with relevant metadata,
    same as columns in Game table

    Attributes:
        title (str): title of the game
        description (str): short description of the game
        release_date (int): unix timestamp of when game was released.
        developer (str): developers of the game
        publisher (str): optional publisher of game, defaults to developer.
        game_id (int): id of game
        image_link (str): link to media image of game from igdb.com
        data (Dict): dict of required values.
    """

    def __init__(self, **data):
        self.title = data.get("title")
        self.description = data.get("description")
        self.release_date = data.get("release_date")
        self.developer = data.get("developer")
        self.image_link = data.get("image_link")
        self.id = data.get("game_id")
        self.publisher = data.get("publisher", self.developer)


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
    game = Game(**data)
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
    game = Game(**data)
    db.commit()
    if game:
        game.release_date = datetime.fromtimestamp(game.release_date)
    return game


def get_games_by_closest_match(matching_text: str) -> list[Game]:
    """
    returns a list of all games in database ordered by how closely the match the given string.

    Args:
        matching_text (str): the text that will be compared to each game
    Returns
        games (List[Game]): a list of games ordered by how closely they match the given text.
    """

    db, cursor = get_database()

    cursor.execute("SELECT * FROM Games")
    data = cursor.fetchall()
    db.commit()

    if not data:
        raise KeyError("No Games Found in Database?!")

    games = []
    for row in data:
        distance = levenshtein_distance(matching_text, row["title"])
        games.append((distance, row))

    games.sort(key=lambda pair: pair[0])
    return games


def add_game(game: Game) -> None:
    """
    Add a new game to the database and its associated platforms and game_tags.

    Args:
        game (Game): game object that contains all relevant information for adding a new game

    Returns:
        None
    """
    db, cursor = get_database()

    game_insert = """
    INSERT INTO Games 
    (title, description, release_date, developer, publisher, image_link)
    VALUES (?,?,?,?,?,?)
    """
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


def update_game(new_game: Game = None):
    """
    Updates Game in database with new values from object.
    Cannot set game tags and platforms, use link for that instead.

    Args:
        new_game (Game): new game data that will overwrite all current data except game_id
    Returns:
        None
    """
    db, cursor = get_database()
    update = """
    UPDATE Games 
    SET title = ?, description = ?, release_date = ?, 
    developer = ?, publisher = ?, image_link = ?
    """
    cursor.execute(
        update,
        (
            new_game.title,
            new_game.description,
            new_game.release_date,
            new_game.developer,
            new_game.publisher,
            new_game.image_link,
        ),
    )
    db.commit()


def delete_game_by_id(game_id: int) -> None:
    """
    Removes a game from Games Table by game_id

    Args:
        game_id (int): The ID of the game to delete.

    Returns:
        None

    """
    db, cursor = get_database()

    delete = "DELETE FROM Games WHERE game_id = ?"
    cursor.execute(delete, (game_id,))

    db.commit()


def link_game_tag(game: Game, game_tag: GameTag) -> None:
    """
    Adds a new row in the GameTagAssingnment table.

    Args:
        game (Game): game that should be linked to a game tag
        game_tag (GameTag): game tag tuple whose id will be used to link to game.
    Returns:
        None
    """
    db, cursor = get_database()

    insert = "SELECT * FROM GameTags WHERE game_tag_id = ?"
    cursor.execute(insert, (game_tag.id,))
    if not cursor.fetchone():
        raise KeyError("game_tag.id doesn't exist in the database.")

    insert = "INSERT INTO GameTagAssignment (game_id, game_tag_id) VALUES (?,?)"
    cursor.execute(insert, (game.id, game_tag.id))

    db.commit()


def link_platform(game: Game, platform: Platform) -> None:
    """
    Adds new row into PlatformAssingment table based on input ids.

    Args:
        game (Game): game that is playable on platform
        platform (platform): platform the game is playable on.
    Returns:
        None
    Raises:
        KeyError: if platform_id is not in database.
    """

    db, cursor = get_database()

    insert = "SELECT * FROM Platforms WHERE platform_id = ?"
    cursor.execute(insert, (platform.id,))
    if not cursor.fetchone():
        raise KeyError("platform.id doesn't exist in the database.")

    insert = "INSERT INTO PlatformAssignment (game_id, platform_id) VALUES (?,?)"
    cursor.execute(insert, (game.id, platform.id))

    db.commit()


# Review Logic

AccessibilityOptions = namedtuple(
    "AccessibilityOptions",
    ["has_colourblind_support", "has_subtitles", "has_difficulty_options"],
)
"""NamedTuple representing accessibilty options that a game can have."""


class Review(object):
    """
    Represents a review with relevant metadata, same as columns in Reviews table.

    Attributes:
        review_id (int): id for the review (same as game_id + user_id)
        user_id (int): id of the user that wrote the review.
        game_id (int): id of the game the review is for.
        rating (int): rating of the review that the user left.
        review_text (text): text that the user has written, optional.
        review_date (int): date the review was uploaded in unix timestamp format.
        accessibility (AccessibilityOptions): Tuple representing accessibilty options for game.
        platform_id (int): the id of the platform the user played the game on.
        data (Dict): Required dict with review values.
    """

    def __init__(self, **data) -> None:
        self.review_id = data["review_id"]
        self.user_id = data["user_id"]
        self.game_id = data["game_id"]
        self.rating = data["rating"]
        self.review_text = data.get("review_text")
        self.review_date = data["review_date"]
        self.accessibility = AccessibilityOptions(
            data["has_colourblind_support"],
            data["has_subtitles"],
            data["has_difficulty_options"],
        )
        self.platform_id = data["platform_id"]



def add_review(review: Review) -> None:
    """
    Adds a new row into Reviews Database. Doesn't need review_id in Review object.

    Args:
        review (Review): review object to use in creating row, review_id can = None.
    Returns:
        None
    """

    db, cursor = get_database()

    insert = """INSERT INTO Reviews (
        user_id, 
        game_id, 
        rating, 
        review_text, 
        review_date, 
        has_colourblind_support, 
        has_subtitles, 
        has_difficulty_options,
        platform_id
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    cursor.execute(
        insert,
        (
            review.user_id,
            review.game_id,
            review.rating,
            review.review_text,
            review.review_date,
            review.accessibility.has_colourblind_support,
            review.accessibility.has_subtitles,
            review.accessibility.has_difficulty_options,
            review.platform_id,
        ),
    )
    db.commit()


def get_review_by_id(review_id: int):
    """
    Returns review with all data using review id to find.

    Args:
        review_id (int): id of review to find.
    Returns:
        review (Review): a review object with relevant data.
    """

    db, cursor = get_database()

    query = "SELECT * FROM Reviews WHERE review_id = ?"
    cursor.execute(query, (review_id,))
    data = cursor.fetchone()
    db.commit()
    review = Review(data=data)
    return review


def get_review_by_game_and_user(game_id: int, user_id: int):
    """
    Returns review with all data using user id and game id to find.

    Args:
        game_id (int): id of game to for review.
        user_id (int): id of user that wrote review.
    Returns:
        review (Review): a review object with relevant data.
    """
    db, cursor = get_database()
    query = "SELECT * FROM Reviews WHERE game_id = ? AND user_id = ?"
    cursor.execute(query, (game_id, user_id))
    data = cursor.fetchone()
    db.commit()
    review = Review(data=data)
    return review


def get_reviews_by_game_name(game_name: str):
    """
    Returns a list of review objects whose game_id is tied to provided game_name.

    Args:
        game_name (str): name of the game to find reviews for.
    Returns:
        reviews (list[Review]): list of review objects with all data.
    """

    db, cursor = get_database()

    query = """
    SELECT 
    r.review_id, r.user_id, r.game_id,
    r.rating, r.review_text, r.review_date, 
    r.has_colourblind_support, r.has_subtitles, r.has_difficulty_options, 
    r.platform_id 
    FROM Reviews r 
    INNER JOIN Games g 
    ON r.game_id = g.game_id
    WHERE g.title = ?
    """
    cursor.execute(query, (game_name,))
    data = cursor.fetchall()
    db.commit()
    reviews = []
    for review_data in data:
        reviews.append(Review(data=review_data))
    return reviews


def get_reviews_by_username(user_name: str):
    """
    Returns a list of review objects whose user_id is linked to provided user_name.

    Args:
        user_name (str): name of the user to find reviews for.
    Returns:
        reviews (list[Review]): list of review objects with all data.
    """

    db, cursor = get_database()

    query = """
    SELECT 
    r.review_id, r.user_id, r.user_id,
    r.rating, r.review_text, r.review_date, 
    r.has_colourblind_support, r.has_subtitles, r.has_difficulty_options, 
    r.platform_id 
    FROM Reviews r 
    INNER JOIN Users u 
    ON r.game_id = u.game_id
    WHERE u.username = ?
    """
    cursor.execute(query, (user_name,))
    data = cursor.fetchall()
    db.commit()
    reviews = []
    for review_data in data:
        reviews.append(Review(data=review_data))
    return reviews

def get_reviews_by_game_and_platform(game_id: int, platform_id: int):
    """
    Returns list of all reviews for a game played on a certain platform.
    Args:
        game_id (int): id of the game the reviews were written for.
        platform_id (int): id of the platform the reviews were written for.
    Returns:
        reviews (List[Review]): list of reviews with relevant metadata.
    """
    db, cursor = get_database()
    query = "SELECT * FROM Reviews WHERE game_id = ? and platform_id = ?"
    cursor.execute(query, game_id, platform_id)
    data = cursor.fetchall()
    db.commit()
    reviews = []
    for row in data:
        review = Review(**row)
        reviews.append(review)
    return reviews

def delete_review_by_id(review_id: int) -> None:
    """
    Removes a review by using it's id.
    Args:
        review_id (int): id of the review that should be deleted.
    Returns:
        None
    """
    db, cursor = get_database()
    delete = "DELETE FROM Reviews WHERE review_id = ?"
    cursor.execute(delete, review_id)
    db.commit()

def update_review(new_review: Review):
    """
    Updates an existing review in the Reviews database table.

    This function edits the rating, review text, and accessibility options
    (colourblind support, subtitles, difficulty options) found by review_id

    Args:
        new_review (Review): A Review object containing the updated review data.
                    Must include a valid review_id corresponding to an existing review.
    """
    db, cursor = get_database()
    update = """
    UPDATE Reviews
    SET rating = ?, 
    review_text = ?   
    has_colourblind_support = ?, 
    has_subtitles = ? ,
    has_difficulty_options = ?
    WHERE review_id = ?
    """
    cursor.execute(update, (new_review.rating,
                            new_review.review_text,
                            new_review.accessibility.has_colourblind_support,
                            new_review.accessibility.has_subtitles,
                            new_review.accessibility.has_difficulty_options,
                            new_review.review_id
                            ))
    db.commit()


# Web App Logic
@app.teardown_appcontext
def close_database_connection(exception):
    """closes database when app has been closed"""
    db = g.pop("db", None)
    if db is not None:
        db.close()
    if exception is not None:
        print(f"ERROR: {exception} RAISED ON CLOSING APP")


@app.route("/home")
def home():
    """
    returns a webpage from template "home.html", called when user goes to /home.
    """
    if not "user_id" in session.keys():
        session["user_id"] = None
    if not session["user_id"] is None:
        user = get_user_by_id(session["user_id"])
        user.date_joined = datetime.fromtimestamp(round(user.date_joined))
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
    """
    login page for site.
    sets session's user id to user's user id if they login successfuly.
    """

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = get_user_by_username(username)
        print(user)
        if user:

            if security.check_password_hash(user.password_hash, password):
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
    """removes user's user_id in the session and sends to home"""
    session["user_id"] = None
    return redirect(url_for("home"))


@app.route("/")
def index():
    """simple redirect from home, only called when first going to website."""
    return redirect(url_for("home"))


# Admin Tools
fake = Faker()


@app.route("/admin")
def admin_page():
    """admin page contains debug tools for database.
    currently doesn't check if user is an admin."""
    return render_template("admin.html")


@app.route("/set_game", methods=["GET", "POST"])
def set_game():
    if request.method == "POST":
        game = Game(**request.form.to_dict(flat=True))
        add_game(game)
        flash(f"added game: {game.title}")
    return redirect(url_for("admin_page"))


@app.route("/write_review", methods=["GET", "POST"])
def write_review():
    if request.method == "POST":
        review = Review(**request.form.to_dict(flat=True))
        add_review(review)
        flash(f"added review for {review.game_id} by {review.user_id}")

    return redirect(url_for("admin_page"))


@app.route("/add_game_tag", methods=["GET", "POST"])
def add_tag():
    if request.method == "POST":
        tag_name = request.form["tag_name"].strip()
        add_game_tag(tag_name)
        flash(f"added tag: {tag_name}.")
    return redirect(url_for("admin_page"))


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
        flash(f"added user: {username} with password: {password}")
    return redirect(url_for("admin_page"))


@app.route("/wipe_users", methods=["GET", "POST"])
def wipe_users():
    if request.method == "POST":
        db, cursor = get_database()
        cursor.execute("DELETE FROM Users")
        cursor.execute("UPDATE sqlite_sequence SET seq=0 WHERE name='Users'")
        db.commit()
        flash("cleared Users Table")
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
