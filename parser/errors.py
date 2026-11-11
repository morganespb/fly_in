class ParseError(Exception):
    """A map file error with the line where it was found"""

    def __init__(
        self, message: str, line_no: int | None = None,
        line: str | None = None) -> None:
        """create the error and build its printable message"""

        self.message: str = message
        self.line_no: int | None = line_no
        self.line: str | None = line
        super().__init__(str(self))

    def __str__(self) -> str:
        """return error message"""
        if self.line_no is None:
            return self.message
        text = f"line {self.line_no}: {self.message}"
        if self.line is not None:
            text += f"\n    {self.line_no} | {self.line}"
        return text
