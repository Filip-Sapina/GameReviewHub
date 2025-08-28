"""
base functions that all other connection files, including classes.
"""

from dataclasses import dataclass
import sqlite3
from typing import Optional, Dict
from flask import g


DATABASE = "database.db"


def make_dicts(cursor, row) -> dict:
    """row factory for database to turn tuples of values into dicts"""
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))


def get_database(database=DATABASE):
    """returns a database connection and cursor object of connection"""

    # If db is not found in global.
    if "db" not in g:
        g.db = sqlite3.connect(database)
        g.db.row_factory = make_dicts

    # Return database connection and cursor.
    cursor = g.db.cursor()
    return g.db, cursor


def query_db(query: str, args=(), fetch: bool = True, one: bool = False):
    """
    Completes a database SQL query on Database.db
    Args:
        query (str): the SQL query that the should be used on database.
        args (tuple): tuple of any arguments the query needs in order as they appear in the query.
        fetch (bool): if true function will return value from query,
        should be false for something like INSERT.
        one (bool): if true function will only fetch first value of query,
        does nothing if fetch = false.
    """
    # Get connection

    db, cursor = get_database()

    # Complete Query
    cursor.execute(query, args)

    # Pull and return data from database if required.
    if fetch:
        if one:
            data = cursor.fetchone()
        else:
            data = cursor.fetchall()
        return data

    # close cursor and commit any changes.
    cursor.close()
    db.commit()


# Data Classes


@dataclass
class User:
    """
    Represents a user with relevant metadata, same as columns in Users table.
    """

    user_id: int
    username: int
    password_hash: str
    date_joined: int

    @classmethod
    def from_dict(cls, data):
        """
        Creates a User from a data object

        Args:
            username (str): name of the user.
            user_id (int): id of the user in Users table.
            pasword_hash (str): hashed version of user's password
            date_joined (int): unix timestamp format of when user made account.
            data (Dict): Required dict with all previous values.
        """
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            password_hash=data["password_hash"],
            date_joined=data["date_joined"],
        )


@dataclass
class GameTag:
    """
    Represents a Game Tag with relevant metadata, same as columns in GameTags table.
    """

    tag_id: int
    name: str


@dataclass
class Platform:
    """
    Represents a platform with relevant metadata, same as columns in Platforms table.
    """

    platform_id: int
    name: str


@dataclass
class Game:
    """
    Represents a video game with relevant metadata,
    same as columns in Game table
    """

    title: str
    description: str
    release_date: int
    developer: str
    publisher: str
    image_link: str
    game_id: int

    @classmethod
    def from_dict(cls, data):
        """
        Creates a Game data object based on provided dict

        Args:
            title (str): title of the game
            description (str): short description of the game
            release_date (int): unix timestamp of when game was released.
            developer (str): developers of the game
            publisher (str): optional publisher of game, defaults to developer.
            game_id (int): id of game
            image_link (str): link to media image of game from igdb.com
            data (Dict): dict of required values.
        """
        return cls(
            title=data["title"],
            description=data["description"],
            release_date=data["release_date"],
            developer=data["developer"],
            publisher=data.get("publisher", data["developer"]),
            image_link=data["image_link"],
            game_id=data["game_id"],
        )


@dataclass
class AccessibilityOptions:
    """Represents possible accessibility options a game can have"""

    has_colourblind_support: bool
    has_subtitles: bool
    has_difficulty_options: bool


@dataclass
class Review:
    """
    Represents a review with relevant metadata, same as columns in Reviews table.
    """

    review_id: Optional[int]  # Computed or nullable
    user_id: int
    game_id: int
    rating: int
    review_text: Optional[str]
    review_date: int  # or datetime, depending on how you use it
    accessibility: AccessibilityOptions
    platform_id: int

    @classmethod
    def from_dict(cls, data: Dict) -> "Review":
        """
        Creates a Review from a dict.
        Args:
            review_id (int): id for the review (same as game_id + user_id)
            user_id (int): id of the user that wrote the review.
            game_id (int): id of the game the review is for.
            rating (int): rating of the review that the user left.
            review_text (text): text that the user has written, optional.
            review_date (int): date the review was uploaded in unix timestamp format.
            accessibility (AccessibilityOptions): Tuple representing accessibilty options for game.
            platform_id (int): the id of the platform the user played the game on.
            data (Dict): Required dict with all previous values.
        """
        return cls(
            review_id=data.get("review_id"),
            user_id=data["user_id"],
            game_id=data["game_id"],
            rating=data["rating"],
            review_text=data.get("review_text"),
            review_date=data["review_date"],
            accessibility=AccessibilityOptions(
                data["has_colourblind_support"],
                data["has_subtitles"],
                data["has_difficulty_options"],
            ),
            platform_id=data["platform_id"],
        )
