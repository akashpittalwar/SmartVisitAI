import base64

def read_image_bytes(path: str) -> bytes:
    """
    Load image data from disk. Used for few-shot examples.
    """
    with open(path, "rb") as f:
        return f.read()

def to_base64(image_bytes: bytes) -> str:
    """
    Convert raw image bytes to base64 string.
    The browser’s FileReader will already give us "data:image/...;base64,...".
    We can strip off the "data:image/png;base64," prefix if needed.
    """
    return base64.b64encode(image_bytes).decode("utf-8")

def from_base64(b64_str: str) -> bytes:
    """
    Decode a base64-encoded string (with or without data URI prefix) into raw bytes.
    Example: "data:image/png;base64,<actualB64>" or just "<actualB64>".
    """
    # If it contains a comma (i.e. data URI), split off the prefix
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    return base64.b64decode(b64_str)
