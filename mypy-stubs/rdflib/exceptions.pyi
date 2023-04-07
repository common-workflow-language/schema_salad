class Error(Exception):
    msg: str
    def __init__(self, msg: str | None = ...) -> None: ...

class ParserError(Error):
    msg: str
    def __init__(self, msg: str) -> None: ...
