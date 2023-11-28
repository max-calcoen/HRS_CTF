import sqlite3

CURR_DIR = "server_resources/2_sql_injection/"

# run from base project directory
connection = sqlite3.connect(CURR_DIR + "db.sqlite")


with open(CURR_DIR + "schema.sql") as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute(
    "INSERT INTO flags (flag) VALUES (?)",
    ("hrs_ctf{v3ry_s3cr3t_FL4G}",),
)

connection.commit()


connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

for el in cursor.fetchall():
    print(el[0])


connection.close()
