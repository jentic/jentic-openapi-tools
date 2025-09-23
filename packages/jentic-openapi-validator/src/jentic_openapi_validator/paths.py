def escape_token(path: str) -> str:
    return path.replace("~", "~0").replace("/", "~1")
