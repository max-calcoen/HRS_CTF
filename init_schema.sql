DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    passhash TEXT NOT NULL,
    gympoints INTEGER DEFAULT 0 NOT NULL,
    completedproblems TEXT DEFAULT "[]"
);
-- sample user
-- admin password: Adm1n
INSERT INTO users (username, passhash)
VALUES (
        "admin",
        "$2b$12$zaDW0OgchpM2Oy6hXSHARuf9KFq3ATiOiJneOCbLkrRDxEWXhbv/m"
    );