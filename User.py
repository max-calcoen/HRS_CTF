class User:
    """Represents a User with the following attributes.

    Attributes:
        id (int): Unique identifier of the user.
        username (str): Username of the user.
        password (bytes): Hashed password of the user.
        points (int): The number of gym points the user has.
        completed_ex (list): List of ids of completed exercises.
    """

    def __init__(self, db_tuple=[0, "", b"", 0, "[]"]):
        """Initializes a User instance from a database tuple.

        Args:
            db_tuple (list): A tuple containing the user data.
                Defaults to a tuple representing a new user.
        """
        self.id = db_tuple[0]  # User ID
        self.username = db_tuple[1]  # Username
        self.password = db_tuple[2]  # Hashed password
        self.points = int(db_tuple[3])  # Points, converted to integer
        # Attempt to parse the completed exercises from the string to a list of integers
        try:
            self.completed_ex = [
                int(ex) for ex in db_tuple[4].strip("[]").split(",") if ex.strip()
            ]
        except:
            self.completed_ex = []

    def __str__(self):
        """Returns a string representation of the user.

        Returns:
            str: A string containing the user ID and username.
        """
        return f"{self.id}: {self.username}"

    def __compare_to(self, other):
        """Compares this user to another based on gym points.

        Args:
            other (User): Another user to compare to.

        Returns:
            bool: True if this user has more points than the other, False otherwise.
        """
        return self.points > other.points

    def __lt__(self, other):
        """Less than comparison based on gym points.

        Args:
            other (User): Another user to compare to.

        Returns:
            bool: Result of comparison with __compare_to method.
        """
        return self.__compare_to(other)
