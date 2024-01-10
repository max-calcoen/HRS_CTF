"""
This script sets up a SQLite database connection to 'users.sqlite' and resets
the users data using a SQL script from 'reset_users.sql'. It is used for
initializing or resetting user data in the database.
"""

import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect("users.sqlite")

# Read SQL commands from 'reset_users.sql' and execute them
with open("reset_users.sql") as f:
    connection.executescript(f.read())

# Commit changes to the database
connection.commit()

# Close the database connection
connection.close()
