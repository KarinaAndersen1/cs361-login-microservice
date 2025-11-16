import secrets


def verify_password(plain_password: str, stored_password: str | None) -> bool:
    """
    Very simple verification for demo purposes:
    - Compares the plain password to the stored password using constant-time compare.

    In a real system you'd store a bcrypt/argon2 hash and verify against that.
    """
    if stored_password is None:
        return False
    return secrets.compare_digest(plain_password, stored_password)
