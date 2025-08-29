from enum import Enum

__all__ = ("BlackDisplay", "Icon")


def _(name: str) -> str:
    return f"assets/{name}.png"


class Icon(Enum):
    app = _("app")
    black_circle = _("black_circle")
    error = _("error")
    example = _("example")
    green_circle = _("green_circle")
    qmark = _("qmark")
    yellow_circle = _("yellow_circle")


class BlackDisplay(Enum):
    querty = "Qwerty"
    abc = "ABC..."
    only_blacks = "Only known blacks"
