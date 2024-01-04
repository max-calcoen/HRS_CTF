DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    passhash TEXT NOT NULL,
    gympoints INTEGER DEFAULT 0 NOT NULL,
    completedexercises TEXT DEFAULT "[]"
);