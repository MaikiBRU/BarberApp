"""Password hashing utilities."""

import bcrypt

#: Cost factor used for new hashes. Higher is slower and safer.
BCRYPT_ROUNDS = 12

#: Hash of a value nobody can supply, used to keep the login path
#: constant-time when the email does not exist.
_DUMMY_HASH = bcrypt.hashpw(
    b"barberapp-timing-equalizer",
    bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
).decode("utf-8")


class PasswordUtils:
    """Password hashing and verification utilities."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password with bcrypt."""
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a stored hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False

    @staticmethod
    def dummy_hash() -> str:
        """Return a throwaway hash for constant-time login checks."""
        return _DUMMY_HASH

    @staticmethod
    def needs_rehash(password_hash: str, min_rounds: int = BCRYPT_ROUNDS)\
            -> bool:
        """Return True when a stored hash uses an outdated cost factor."""
        if not password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            return True
        try:
            return int(password_hash.split("$")[2]) < min_rounds
        except (IndexError, ValueError):
            return True
