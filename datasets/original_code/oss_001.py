def validate_email(email: str) -> bool:
    """Validate email address format using regex.

    Args:
        email: Email address string to validate

    Returns:
        True if email format is valid, False otherwise
    """
    import re

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
