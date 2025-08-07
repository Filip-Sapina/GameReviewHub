from datetime import datetime
from thefuzz import fuzz
from database_connection.base_db_connections import query_db
from database_connection.review_connection import get_reviews_by_game_id
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


def get_games():
    """
    Returns All Games in the Database.
    """
    data = query_db("SELECT * FROM Games")

    if data is None:
        raise KeyError("No Games Found in Database?!")

    games = []

    for row in data:
        game = Game(**row)
        games.append(game)

    return games


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

    data = query_db(
        "SELECT * FROM Games WHERE game_id = ?", (game_id,), fetch=True, one=True
    )
    game = Game(**data)
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

    data = query_db(
        "SELECT * FROM Games WHERE title = ?", (game_name,), fetch=True, one=True
    )
    game = Game(**data)
    if game:
        game.release_date = datetime.fromtimestamp(game.release_date)
    return game


def get_games_by_closest_match(matching_text: str) -> list[Game]:
    """
    returns a list of most games in database ordered by how closely the match the given string.
    Ignores games under specific ratio so that unrelated games are less common.

    Args:
        matching_text (str): the text that will be compared to each game
    Returns
        games (List[Game]): a list of games ordered by how closely they match the given text.
    """

    data = query_db("SELECT * FROM Games", fetch=True, one=False)

    if not data:
        raise KeyError("No Games Found in Database?!")

    games = []
    for row in data:
        game = Game(**row)
        closeness = fuzz.ratio(matching_text, game.title)
        if closeness > 20:
            games.append((closeness, game))

    games.sort(key=lambda pair: pair[0], reverse=True)
    games = [pair[1] for pair in games]
    return games


def get_games_by_platform_ids(platform_ids: list[int]):
    """
    Returns a list of Game objects ordered by how many of the input platform_ids they are assigned.

    Args:
        platform_ids (List[int]): List of platform IDs to match.

    Returns:
        List[Game]: List of Game objects, ordered by match count descending.
    """

    if not platform_ids:
        return []

    query = """
        SELECT 
            Games.*, 
            COUNT(PlatformAssignment.game_tag_id) as tag_match_count
        FROM Games
        JOIN PlatformAssignment ON Games.game_id = PLatformAssignment.game_id
        WHERE PLatformAssignment.game_tag_id IN (?)
        GROUP BY Games.game_id
        ORDER BY tag_match_count DESC
    """
    data = query_db(query, platform_ids, fetch=True, one=False)

    games = []
    for row in data:
        game = Game(**row)
        games.append(game)
    return games


def get_games_by_game_tag_ids(game_tag_ids: list[int]):
    """
    Returns a list of Game objects ordered by how many of the input game_ids they are assigned.

    Args:
        game_ids (List[int]): List of game IDs to match.

    Returns:
        List[Game]: List of Game objects, ordered by match count descending.
    """

    if not game_tag_ids:
        return []

    query = """
        SELECT 
            Games.*, 
            COUNT(GameTagAssignment.game_tag_id) as tag_match_count
        FROM Games
        JOIN GameTagAssignment ON Games.game_id = GameTagAssignment.game_id
        WHERE GameTagAssignment.game_tag_id IN (?)
        GROUP BY Games.game_id
        ORDER BY tag_match_count DESC
    """

    data = query_db(query, game_tag_ids, fetch=True, one=False)
    games = []
    for row in data:
        game = Game(**row)
        games.append(game)
    return games


def add_game(game: Game) -> None:
    """
    Add a new game to the database and its associated platforms and game_tags.

    Args:
        game (Game): game object that contains all relevant information for adding a new game

    Returns:
        None
    """
    game_insert = """
    INSERT INTO Games 
    (title, description, release_date, developer, publisher, image_link)
    VALUES (?,?,?,?,?,?)
    """
    args = (
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

    query_db(game_insert, args, fetch=False, one=False)


def update_game(new_game: Game = None):
    """
    Updates Game in database with new values from object.
    Cannot set game tags and platforms, use link for that instead.

    Args:
        new_game (Game): new game data that will overwrite all current data except game_id
    Returns:
        None
    """

    update = """
    UPDATE Games 
    SET title = ?, description = ?, release_date = ?, 
    developer = ?, publisher = ?, image_link = ?
    """
    args = (
        new_game.title,
        new_game.description,
        new_game.release_date,
        new_game.developer,
        new_game.publisher,
        new_game.image_link,
    )
    query_db(update, args, fetch=False, one=False)


def delete_game_by_id(game_id: int) -> None:
    """
    Removes a game from Games Table by game_id

    Args:
        game_id (int): The ID of the game to delete.

    Returns:
        None

    """
    query_db("DELETE FROM Games WHERE game_id = ?", (game_id,), fetch=False, one=False)


def link_game_tag(game_id: int, game_tag_id: int) -> None:
    """
    Adds a new row in the GameTagAssingnment table.

    Args:
        game_id (int): game that should be linked to a game tag
        game_tag_id (int): game tag tuple whose id will be used to link to game.
    Returns:
        None
    """
    query_db(
        "INSERT INTO GameTagAssignment (game_id, game_tag_id) VALUES (?,?)",
        (game_id, game_tag_id),
        fetch=False,
        one=False,
    )


def link_platform(game_id: int, platform_id: int) -> None:
    """
    Adds new row into PlatformAssingment table based on input ids.

    Args:
        game_id (int): game that is playable on platform
        platform_id (platform_id): platform the game is playable on.
    Returns:
        None
    """
    query_db(
        "INSERT INTO PlatformAssignment (game_id, platform_id) VALUES (?,?)",
        (game_id, platform_id),
        fetch=False,
        one=False,
    )


def get_avg_rating(game_id: int):
    """
    returns average rating for a game based on reviews.
    Args:
        game_id (int): id of game to find rating
    Returns:
        avg_rating (int): number between 1-10 inclusive showing rating
    """
    reviews = get_reviews_by_game_id(game_id)

    # Check to prevent dividing by zero.
    if len(reviews) == 0:
        return "N/A"

    # adds all ratings up and divides by the amount of reviews.
    total = sum(review.rating for review in reviews)
    average = round(total / len(reviews), 2)

    return average
