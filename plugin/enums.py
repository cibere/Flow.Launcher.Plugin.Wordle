from enum import Enum, EnumMeta
from enum import auto as _auto


class StatusEnum(Enum):
    green = _auto()
    yellow = _auto()
    black = _auto()


class DisplayBlackSettingEnum(Enum):
    querty = "Qwerty"
    abc = "ABC"
    only_blacks = "Only known blacks"
