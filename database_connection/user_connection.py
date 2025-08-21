"""functions that allow connection between database and web app specifically for users."""

from datetime import datetime
from flask import session
from werkzeug import security
from database_connection.base_db_connections import query_db, User

# if not logged in, use default user, sort of like guest.
DEFAULT_USER = {
    "user_id": None,
    "username": None,
    "password_hash": None,
    "date_joined": None,
}


class UserConnector:
    """class that contains user related functions for the database"""

    def __init__(self) -> None:
        pass

    def get_user_by_id(self, user_id: int) -> User:
        """
        Returns user data from database using user_id

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            user (User): object containing each column of found row in database.
        Raises:
            TypeError: If user_id is not an integer.
        """
        data = query_db(
            """
            SELECT 
            u.user_id, 
            u.username, 
            u.password_hash, 
            u.date_joined 
            FROM Users u 
            WHERE user_id = ?
            """,
            (user_id,),
            fetch=True,
            one=True,
        )
        user = User.from_dict(data)
        return user

    def get_user_by_username(self, username: str) -> User:
        """
        Returns user data from database using username

        Args:
            username (str): The name of the user to retrieve.

        Returns:
            user (User): object containing each column of found row in database.

        Raises:
            TypeError: If username is not an string.
        """
        data = query_db(
            """SELECT 
            u.user_id, 
            u.username, 
            u.password_hash, 
            u.date_joined 
            FROM Users u  
            WHERE username = ?
            """,
            (username,),
            fetch=True,
            one=True,
        )

        # Check to prevent making a User with None data which causes an error.
        if data is None:
            return None

        user = User.from_dict(data)
        return user

    def get_user_session(self):
        """
        returns the user if logged into user session, other returns default n/a user.
        """
        # if user_id is not in session keys, user is not logged in.
        if not "user_id" in session.keys():
            session["user_id"] = None

        if not session["user_id"] is None:
            # user is logged in, therefore can get user object
            user = self.get_user_by_id(session["user_id"])
            user.date_joined = datetime.fromtimestamp(round(user.date_joined))
        else:
            # not logged in so default user
            user = User.from_dict(DEFAULT_USER)
        return user

    def add_user(self, username: str, password: str) -> None:
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
        query_db(
            "INSERT INTO Users (username, password_hash, date_joined) VALUES (?,?,?)",
            (username, password_hash, date_joined),
            fetch=False,
        )

    def delete_user_by_id(self, user_id: int) -> None:
        """
        Removes a user from Users Table by user_id

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            None

        """
        query_db("DELETE FROM Users WHERE user_id = ?", (user_id,))

    def update_user(
        self, user_id: int, username: str = None, password: str = None
    ) -> None:
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

        query = "UPDATE Users SET "
        values = ()
        if username:
            query = query + username
            values = (*values, username)
        if password:
            password_hash = security.generate_password_hash(password)
            query = query + password_hash
            values = (*values, password_hash)
        query = query + "WHERE user_id = ?"
        values = (*values, user_id)
        query_db(query, values, fetch=False)
