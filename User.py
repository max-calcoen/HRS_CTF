class User:
    def __init__(self, db_tuple):
        self.id = db_tuple[0]
        self.username = db_tuple[1]
        self.password = db_tuple[2]
        self.points = int(db_tuple[3])
        try:
            self.completed_ex = [int(ex) for ex in db_tuple[4].strip("[]").split(",")]
        except:
            self.completed_ex = []

    def __str__(self):
        return f"{self.id}: {self.username}"
