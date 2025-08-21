"""functions that allow connection between database and web app specifically for platforms 
(playstation 5, xbox one, etc)."""

from database_connection.base_db_connections import query_db
from database_connection.base_db_connections import Platform, GameTag


class PlatformConnector:
    """class that contains platform related functions for the database"""
    def __init__(self) -> None:
        pass

    def add_platform(self, platform_name: str) -> None:
        """
        Adds a new platform row to Platforms table in database.
        Args:
            platform (str): platform's name.
        Returns:
            None
        """
        query_db(
            "INSERT INTO Platforms (platform_name) VALUES (?)",
            (platform_name,),
            fetch=False,
            one=False,
        )

    def delete_platform_by_id(self, platform_id: int):
        """
        Deletes a platform row in database using id.
        Args:
            platform_id (int): id of platform to delete
        Returns:
            None
        """
        query_db(
            "DELETE FROM Platforms WHERE platform_id = ?",
            (platform_id,),
            fetch=False,
            one=False,
        )

    def update_platform(self, new_platform: Platform):
        """
        effectively changes the name of the platform with the given id.

        Args:
            (Platform): id of current platform and name to update
        Returns:
            None
        """
        query_db(
            "UPDATE Platforms SET platform_name = ? WHERE platform_id = ?",
            (new_platform.name, new_platform.id),
            fetch=False,
            one=False,
        )

    def get_platforms(self) -> list[Platform]:
        """
        Returns a list of all platforms.
        """
        data = query_db("SELECT p.platform_id, p.platform_name FROM Platforms p")
        platforms = []
        for tag in data:
            platforms.append(GameTag(tag["platform_id"], tag["platform_name"]))
        return platforms

    def get_platforms_by_game_name(self, game_name: str) -> list[Platform]:
        """
        gets a list of platforms that a game is playable on.

        Args:
            game_name (str): title of game to find platforms for
        Returns:
            platforms: (list[Platform]): A list of Platform namedTuples with id and name
        Raises:
            TypeError: if game_name is not a string.
        """

        platform_ids = query_db(
            """
                SELECT platform_id FROM Games g 
                JOIN PlatformAssignment p ON 
                g.game_id = p.game_id WHERE g.title = ?
                """,
            (game_name,),
            fetch=True,
            one=False,
        )

        platforms = []
        for platform_dict in platform_ids:
            tag = self.get_platform_by_id(platform_dict["platform_id"])
            platforms.append(tag)
        return platforms

    def get_platform_by_name(self, platform_name: str) -> Platform:
        """
        Returns platform row from database using name.

        Args:
            platform_name (str): The name of the game tag to retrieve.

        Returns:
            Platform (NameTuple): a tuple with id and name.

        Raises:
            TypeError: If platform_name is not an string.
        """

        data = query_db(
            "SELECT p.platform_id, p.platform_name FROM Platforms p WHERE platform_name = ?",
            (platform_name,),
            fetch=True,
            one=True,
        )

        return Platform(data["platform_id"], data["platform_name"])

    def get_platform_by_id(self, platform_id: int) -> Platform:
        """
        Returns platform row from database using id.

        Args:
            platform_id (str): The id of the game tag to retrieve.

        Returns:
            Platform (NamedTuple): a tuple with id and name.

        """
        data = query_db(
            "SELECT p.platform_id, p.platform_name FROM Platforms p WHERE platform_id = ?",
            (platform_id,),
            fetch=True,
            one=True,
        )
        return Platform(data["platform_id"], data["platform_name"])
