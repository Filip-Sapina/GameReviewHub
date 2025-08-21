"""functions that allow connection between database and web app specifically for game tags (adventure, fighting, etc)."""

from database_connection.base_db_connections import query_db, GameTag

# Game Tag Logic


class GameTagConnector:
    def __init__(self) -> None:
        pass

    def add_game_tag(self, name: str) -> None:
        """
        Adds a new game tag into the GameTags database

        Args:
            name (str): the name of the game tag

        Returns:
            None
        """
        query_db("INSERT INTO GameTags (game_tag_name) VALUES (?)", (name,), fetch=False)

    def get_game_tags(self) -> list[GameTag]:
        """
        Returns a list of all game tags.
        """
        data = query_db("SELECT gt.game_tag_id, gt.game_tag_name FROM GameTags gt")
        game_tags = []
        for tag in data:
            game_tags.append(GameTag(tag["game_tag_id"], tag["game_tag_name"]))
        return game_tags

    def get_tags_by_game_name(self, game_name: str) -> list[GameTag]:
        """
        gets a list of game tags associated with the game

        Args:
            game_name (str): title of game to find tags of
        Returns:
            tags: (list[GameTag]): A list of GameTag namedTuples with id and name
        Raises:
            TypeError: if game_name is not a string.
        """
        query = """
                SELECT game_tag_id FROM Games g
                JOIN GameTagAssignment gt 
                ON g.game_id = gt.game_id WHERE g.title = ?
                """
        data = query_db(query, (game_name,))
        tags = []
        for tag_dict in data:
            tag = self.get_game_tag_by_id(tag_dict["game_tag_id"])
            tags.append(tag)
        return tags

    def get_game_tag_by_name(self, tag_name: str) -> GameTag:
        """
        Returns game tag row from database using name.

        Args:
            tag_name (str): The name of the game tag to retrieve.

        Returns:
            GameTag (NameTuple): a tuple with id and name.

        Raises:
            TypeError: If tag_name is not an string.
        """
        data = query_db(
            "SELECT gt.game_tag_id, gt.game_tag_name FROM GameTags gt WHERE game_tag_name = ?",
            (tag_name,),
            fetch=True,
            one=True,
        )
        return GameTag(data["game_tag_id"], data["game_tag_name"])

    def get_game_tag_by_id(self, tag_id: int) -> GameTag:
        """
        Returns game tag row from database using id.

        Args:
            id (int): The id of the game tag to retrieve.

        Returns:
            GameTag (NameTuple): a tuple with name and id.

        Raises:
            TypeError: If tag_id is not an integer.
        """
        data = query_db(
            "SELECT gt.game_tag_id, gt.game_tag_name FROM GameTags gt WHERE game_tag_id = ?",
            (tag_id,),
            fetch=True,
            one=True,
        )
        return GameTag(data["game_tag_id"], data["game_tag_name"])

    def update_game_tag(self, new_tag: GameTag):
        """
        effectively changes the name of the gametag with the given id.

        Args:
            new_tag (GameTag): id of current tag and name to update
        Returns:
            None
        """
        query_db(
            "UPDATE GameTags SET game_tag_name = ? WHERE game_tag_id = ?",
            (new_tag,),
            fetch=False,
        )

    def delete_game_tag_by_id(self, tag_id: int):
        """
        Deletes game tag in the GameTags table and removes all connections
        to game tag in GameTagAssignment table.

        Args:
            tag_id (int): id of the game_tag that will be deleted
        Returns:
            None
        """
        query_db(
            "DELETE FROM GameTags WHERE game_tag_id = ?",
            (tag_id,),
            fetch=False,
            one=False,
        )

        # Removes any links to now removed game tag to avoid ghost game tags.
        query_db(
            "DELETE FROM GameTagAssignment WHERE game_tag_id = ?",
            (tag_id,),
            fetch=False,
            one=False,
        )
