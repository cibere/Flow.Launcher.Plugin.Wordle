from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from flogin import Glyph, Result, Query

from .enums import DisplayBlackSettingEnum, StatusEnum
from .errors import CorrectGuess, InvalidGuess, OutOfGuesses, RepeatGuess
from .results import PastGuess, BlackLettersResult

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .plugin import WordlePlugin


class WordleGame:
    def __init__(self, word: str, plugin: WordlePlugin) -> None:
        self.word = word
        self.guesses: list[PastGuess] = []
        self.blacks: set[str] = set()
        self.chars: list[tuple[str, StatusEnum]] = [
            (char, StatusEnum.black) for char in word
        ]
        self.plugin = plugin

    @property
    def greens(self) -> list[str]:
        return [
            char if status is StatusEnum.green else "_" for char, status in self.chars
        ]

    @property
    def yellows(self) -> list[str]:
        return [char for char, status in self.chars if status is StatusEnum.yellow]

    @property
    def remaining_guesses(self) -> int:
        return 6 - len(self.guesses)

    def guess(self, guess: str) -> None:
        if guess == self.word:
            raise CorrectGuess()

        if len(guess) != 5:
            raise InvalidGuess()
        if guess in self.guesses:
            raise RepeatGuess(guess)

        guess_data = []

        for idx, char in enumerate(guess):
            log.debug(f"Checking for {char!r} at {idx!r}")
            if self.word[idx] == char:
                log.debug(f"Setting {char!r} to green")
                self.chars[idx] = char, StatusEnum.green
                guess_data.append((char, StatusEnum.green))
            elif char in self.word:
                log.debug("Yellow detected")
                guess_data.append((char, StatusEnum.yellow))
                for chidx, charinfo in enumerate(self.chars):
                    xchar, status = charinfo
                    if xchar == char and status is not StatusEnum.green:
                        log.debug(f"Setting {char!r} at {chidx!r} to yellow")
                        self.chars[chidx] = char, StatusEnum.yellow
            else:
                guess_data.append((char, StatusEnum.black))
                self.blacks.add(char)

        self.guesses.append(PastGuess(guess_data, len(self.guesses)))

        if len(self.guesses) == 6:
            raise OutOfGuesses()

    def generate_state_results(self, query: Query) -> list[Result]:
        return [
            Result(
                " ".join([char if char else "_" for char in self.greens]),
                icon="Images/green_circle.png",
                score=50,
            ),
            BlackLettersResult(setting=DisplayBlackSettingEnum(self.plugin.settings.black_letters_display_type), blacks=self.blacks, query=query),
        ] + self.guesses
