from ..markdown import Markdown

__all__ = ["math", "math_in_quote", "math_in_list"]

def math(md: Markdown) -> None: ...
def math_in_quote(md: Markdown) -> None: ...
def math_in_list(md: Markdown) -> None: ...
