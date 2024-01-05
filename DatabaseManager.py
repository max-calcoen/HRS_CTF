import sqlite3
from User import User
from json import dumps


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def __connect(self):
        return sqlite3.connect(self.db_path)

    def get_user(self, user_id):
        connection = self.__connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        res = cursor.fetchone()
        user = User(res)
        connection.close()
        return user

    def get_users(self):
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
