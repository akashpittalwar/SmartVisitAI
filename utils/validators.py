import re

def is_valid_phone(phone: str) -> bool:
    """
    Checks a basic international phone format: digits, spaces, +, hyphens.
    Length 7–15 characters. This is not comprehensive, but suffices for our use case.
    """
    phone = phone.strip()
    return bool(re.fullmatch(r"[+\d\s\-]{7,15}", phone))

def is_valid_email(email: str) -> bool:
    """
    Very simple email regex: one or more non-"@" + "@" + one or more non-"@" + "." + one or more non-"@". Note: This doesn’t enforce all RFC rules.
    """
    email = email.strip()
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))

