import sqlite3
from User import User
from json import dumps


class DatabaseManager:
    """Manages the database operations for User objects.

    Attributes:
        db_path (str): Path to the database file.
    """

    def __init__(self, db_path):
        """Initializes the DatabaseManager with the given database path.

        Args:
            db_path (str): The path to the sqlite3 database file.
        """
        self.db_path = db_path

    def __connect(self):
        """Establishes and returns a connection to the database.

        Returns:
            sqlite3.Connection: Connection object to the database.
        """
        return sqlite3.connect(self.db_path)

    def get_user(self, user_id):
        """Fetches a single user from the database by user id.

        Args:
            user_id (int): The unique identifier for the user.

        Returns:
            User: The User object if found, otherwise None.
        """
        connection = self.__connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        res = cursor.fetchone()
        connection.close()
        if res is None:
            return None
        return User(res)

    def get_user_id(self, username):
        """Fetches the user id for a user with a given username.

        Args:
            username (str): The username of the user.

        Returns:
            int/False: The user id if found, otherwise False.
        """
        connection = self.__connect()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        res = cursor.fetchone()
        connection.close()
        return res[0] if res else False

    def get_users(self):
        """Fetches all users from the database.

        Returns:
            list[User]/False: List of User objects if fetch is successful, otherwise False.
        """
        connection = self.__connect()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM users")
            res = cursor.fetchall()
            users = [User(user) for user in res]
        except:
            users = False
        connection.close()
        return users

    def update_user(self, user):
        """Updates an existing user's information in the database.

        Args:
            user (User): The user object with updated information.
        """
        connection = self.__connect()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE users SET username = ?, passhash = ?, gympoints = ?, completedexercises = ? WHERE id = ?",
            (
                user.username,
                user.password,
                user.points,
                dumps(user.completed_ex),
                user.id,
            ),
        )
        connection.commit()
        connection.close()

    def add_user(self, user):
        """Adds a new user to the database.

        Args:
            user (User): The user object to be added.

        Returns:
            int: The id of the newly added user.
        """
        connection = self.__connect()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, passhash, gympoints, completedexercises) VALUES (?, ?, ?, ?)",
            (user.username, user.password, user.points, dumps(user.completed_ex)),
        )
        connection.commit()
        cursor.execute("SELECT id FROM users WHERE username=?", (user.username,))
        user.id = cursor.fetchone()[0]
        connection.close()
        return user.id
