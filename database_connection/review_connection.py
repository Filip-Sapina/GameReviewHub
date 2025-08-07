from collections import namedtuple
from database_connection.base_db_connections import query_db

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
        self.review_id = data.get("review_id")
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
    query_db(
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
        fetch=False,
        one=False,
    )


def get_review_by_id(review_id: int):
    """
    Returns review with all data using review id to find.

    Args:
        review_id (int): id of review to find.
    Returns:
        review (Review): a review object with relevant data.
    """

    data = query_db(
        "SELECT * FROM Reviews WHERE review_id = ?", (review_id,), fetch=True, one=True
    )
    review = Review(data=data)
    return review


def get_reviews_by_game_id(game_id: int):
    """
    Returns review with all data using user id and game id to find.

    Args:
        game_id (int): id of game that has review.
    Returns:
        review (Review): a review object with relevant data.
    """
    query = "SELECT * FROM Reviews WHERE game_id = ?"
    data = query_db(query, (game_id,), fetch=True, one=False)

    reviews = []
    for row in data:
        review = Review(**row)
        reviews.append(review)

    return reviews


def get_review_by_game_and_user(game_id: int, user_id: int):
    """
    Returns review with all data using user id and game id to find.

    Args:
        game_id (int): id of game that has review.
        user_id (int): id of user that wrote review.
    Returns:
        review (Review): a review object with relevant data.
    """
    data = query_db(
        "SELECT * FROM Reviews WHERE game_id = ? AND user_id = ?",
        (game_id, user_id),
        fetch=True,
        one=True,
    )
    review = Review(**data)
    return review


def get_reviews_by_game_name(game_name: str):
    """
    Returns a list of review objects whose game_id is tied to provided game_name.

    Args:
        game_name (str): name of the game to find reviews for.
    Returns:
        reviews (list[Review]): list of review objects with all data.
    """

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
    data = query_db(query, (game_name,), fetch=True, one=False)
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
    data = query_db(query, (user_name,), fetch=True, one=False)
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
    data = query_db(
        "SELECT * FROM Reviews WHERE game_id = ? and platform_id = ?",
        (game_id, platform_id),
        fetch=True,
        one=False,
    )
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
    query_db(
        "DELETE FROM Reviews WHERE review_id = ?", (review_id,), fetch=False, one=False
    )


def update_review(new_review: Review, review_id: int):
    """
    Updates an existing review in the Reviews database table.

    This function edits the rating, review text, and accessibility options
    (colourblind support, subtitles, difficulty options) found by review_id

    Args:
        new_review (Review): A Review object containing the updated review data.
                    Must include a valid review_id corresponding to an existing review.
    """
    update = """
    UPDATE Reviews
    SET rating = ?, 
    review_text = ?,   
    has_colourblind_support = ?, 
    has_subtitles = ? ,
    has_difficulty_options = ?,
    platform_id = ?
    WHERE review_id = ?
    """
    values = (
        new_review.rating,
        new_review.review_text,
        new_review.accessibility.has_colourblind_support,
        new_review.accessibility.has_subtitles,
        new_review.accessibility.has_difficulty_options,
        new_review.platform_id,
        review_id,
    )

    query_db(update, values, fetch=False, one=False)
