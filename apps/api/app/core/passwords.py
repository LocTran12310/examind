import secrets

# No 0/O, 1/l/I — temp passwords are read off paper by students.
ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"


def temp_password(length: int = 10) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
