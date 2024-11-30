from enum import Enum, EnumMeta
from enum import auto as _auto

class StatusEnum(Enum):
    green = _auto()
    yellow = _auto()
    black = _auto()

class DisplayBlackSettingEnum(Enum):
    querty = "Qwerty"
    abc = "ABCDEFG..."
    only_blacks = "Only show known blacks"