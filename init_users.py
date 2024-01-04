import sqlite3

connection = sqlite3.connect("users.sqlite")


with open("reset_users.sql") as f:
    connection.executescript(f.read())

connection.commit()


connection.close()
