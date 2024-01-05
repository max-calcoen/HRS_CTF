import sqlite3


connection = sqlite3.connect("container/db.sqlite")
with open("schema.sql") as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute(
    "INSERT INTO flags (flag) VALUES (?)",
    ("hrs_ctf{v3ry_s3cr3t_FL4G}",),
)

connection.commit()
connection.close()
print("DONE")
