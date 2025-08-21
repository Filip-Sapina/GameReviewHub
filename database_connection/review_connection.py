"""functions that allow connection between database and web app specifically for user reviews."""

from database_connection.base_db_connections import (
    query_db,
    Review,
)


class ReviewConnector:
    """class that contains review related functions for the database"""
    def __init__(self) -> None:
        pass

    def add_review(self, review: Review) -> None:
        """
        Adds a new row into Reviews Database. Doesn't need review_id in Review object.

        Args:
            review (Review): review object to use in creating row, review_id can = None.
        Returns:
            None
        """
        # Insert query.
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
        # query with specified args.
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

    def get_review_by_id(self, review_id: int):
        """
        Returns review with all data using review id to find.

        Args:
            review_id (int): id of review to find.
        Returns:
            review (Review): a review object with relevant data.
        """
        # Query
        data = query_db(
            """
            SELECT 
            r.review_id, 
            r.user_id, 
            r.game_id, 
            r.rating, 
            r.review_text, 
            r.review_date, 
            r.has_colourblind_support, 
            r.has_subtitles, 
            r.has_difficulty_options, 
            platform_id 
            FROM Reviews r WHERE review_id = ?""",
            (review_id,),
            fetch=True,
            one=True,
        )
        # Turn data into review object and return data.
        review = Review.from_dict(data)
        return review

    def get_reviews_by_game_id(self, game_id: int):
        """
        Returns review with all data using user id and game id to find.

        Args:
            game_id (int): id of game that has review.
        Returns:
            review (Review): a review object with relevant data.
        """
        # Query and get Data.
        query = """
        SELECT 
        r.review_id, 
        r.user_id, 
        r.game_id, 
        r.rating, 
        r.review_text, 
        r.review_date, 
        r.has_colourblind_support, 
        r.has_subtitles, 
        r.has_difficulty_options, 
        platform_id FROM Reviews 
        r WHERE game_id = ?"""
        data = query_db(query, (game_id,), fetch=True, one=False)

        # create a list of reviews with data and return.
        reviews = [Review.from_dict(row) for row in data]
        return reviews

    def get_review_by_game_and_user(self, game_id: int, user_id: int):
        """
        Returns review with all data using user id and game id to find.

        Args:
            game_id (int): id of game that has review.
            user_id (int): id of user that wrote review.
        Returns:
            review (Review): a review object with relevant data.
        """

        # Get Review.
        data = query_db(
            """
            SELECT 
            r.review_id, 
            r.user_id, 
            r.game_id, 
            r.rating, 
            r.review_text, 
            r.review_date, 
            r.has_colourblind_support, 
            r.has_subtitles, 
            r.has_difficulty_options, 
            platform_id 
            FROM Reviews r 
            WHERE game_id = ? AND user_id = ?""",
            (game_id, user_id),
            fetch=True,
            one=True,
        )
        # Return review as class.
        review = Review.from_dict(data)
        return review

    def get_reviews_by_game_name(self, game_name: str):
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
            reviews.append(Review.from_dict(review_data))
        return reviews

    def get_reviews_by_username(self, user_name: str):
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
            reviews.append(Review.from_dict(review_data))
        return reviews

    def get_reviews_by_game_and_platform(self, game_id: int, platform_id: int):
        """
        Returns list of all reviews for a game played on a certain platform.
        Args:
            game_id (int): id of the game the reviews were written for.
            platform_id (int): id of the platform the reviews were written for.
        Returns:
            reviews (List[Review]): list of reviews with relevant metadata.
        """
        data = query_db(
            """
            SELECT 
            r.review_id, 
            r.user_id, 
            r.game_id, 
            r.rating, 
            r.review_text, 
            r.review_date, 
            r.has_colourblind_support, 
            r.has_subtitles, 
            r.has_difficulty_options, 
            platform_id FROM Reviews 
            r WHERE game_id = ? and platform_id = ?""",
            (game_id, platform_id),
            fetch=True,
            one=False,
        )
        reviews = []
        for row in data:
            review = Review.from_dict(row)
            reviews.append(review)
        return reviews

    def delete_review_by_id(self, review_id: int) -> None:
        """
        Removes a review by using it's id.
        Args:
            review_id (int): id of the review that should be deleted.
        Returns:
            None
        """
        query_db(
            "DELETE FROM Reviews WHERE review_id = ?",
            (review_id,),
            fetch=False,
            one=False,
        )

    def update_review(self, new_review: Review, review_id: int):
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

    def get_accessibilty_ratios(self, game_id: int):
        """
        Returns the ratio between how many reviews think a 
        game has a acessibilty option vs how many don't.
        Args:
            game_id (int): id of the game that should be checked.
        Returns:
            has_colourblind_support (float):
            has_subtitles (float):
            has_difficulty_options (float):
        """
        reviews = self.get_reviews_by_game_id(game_id)
        # Get Review Count
        review_count = len(reviews)
        # get amount of reviews with each accessibilty setting.
        if review_count > 0:
            has_colourblind_support = 0
            has_difficulty_options = 0
            has_subtitles = 0
            for review in reviews:
                if review.accessibility.has_colourblind_support:
                    has_colourblind_support += 1
                if review.accessibility.has_difficulty_options:
                    has_difficulty_options += 1
                if review.accessibility.has_subtitles:
                    has_subtitles += 1
            has_colourblind_support = int(has_colourblind_support / review_count * 100)
            has_difficulty_options = int(has_difficulty_options / review_count * 100)
            has_subtitles = int(has_subtitles / review_count * 100)
            return (has_colourblind_support, has_subtitles, has_difficulty_options)
        return (0, 0, 0)
