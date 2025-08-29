from __future__ import annotations

import random
from pathlib import Path
from typing import Literal, TypedDict, TypeVar, Unpack, overload

from .enums import CharStatus
from .errors import InvalidGuessLength, OutOfGuesses, RepeatGuess, WordNotFound
from .utils import IndexableDict, SequenceProxy, cached_property

CHARS = "qwertyuiopasdghjklzxcvbnm"
T = TypeVar("T")

__all__ = ("WordleGame",)


class WordleOptions(TypedDict, total=False):
    amount_of_guesses: int
    valid_words: list[str]


class WordleGame:
    def __init__(
        self, word: str | None = None, **options: Unpack[WordleOptions]
    ) -> None:
        self.options = options
        self.word = word or random.choice(self.valid_words)

        self._guesses: IndexableDict[str, list[tuple[str, CharStatus]]] = (
            IndexableDict()
        )
        self._black_chars: set[str] = set()
        self._yellow_chars: set[str] = set()
        self._status: list[tuple[str, CharStatus | None]] = [
            (char, None) for char in self.word
        ]

    def status(self, filler: T = None) -> list[str | T]:
        return [filler if status is None else char for char, status in self._status]

    @property
    def green_chars(self) -> list[str]:
        return [char for char in self.status() if char is not None]

    @property
    def black_chars(self) -> SequenceProxy[str]:
        return SequenceProxy(self._black_chars)

    @property
    def yellow_chars(self) -> SequenceProxy[str]:
        return SequenceProxy(self._yellow_chars)

    def all_chars(self) -> dict[str, CharStatus]:
        return (
            dict.fromkeys(self._black_chars, CharStatus.black)
            | dict.fromkeys(self._yellow_chars, CharStatus.yellow)
            | dict.fromkeys(self.green_chars, CharStatus.green)
        )

    @property
    def past_guesses(self) -> SequenceProxy[list[tuple[str, CharStatus]]]:
        return self._guesses.values

    @property
    def amount_of_guesses(self) -> int:
        return self.options.get("amount_of_guesses", 6)

    @cached_property
    def valid_words(self) -> list[str]:
        if "valid_words" in self.options:
            return self.options["valid_words"]

        words_file = Path(__file__).parent / "word_list.txt"
        return words_file.read_text("UTF-8").splitlines()

    @property
    def guess_length(self) -> int:
        return len(self.word)

    @property
    def remaining_guesses(self) -> int:
        return self.amount_of_guesses - len(self._guesses)

    @overload
    def validate_guess(
        self, guess: str, *, raise_error: Literal[True]
    ) -> Literal[True]: ...
    @overload
    def validate_guess(self, guess: str) -> bool: ...
    def validate_guess(self, guess: str, *, raise_error: bool = False) -> bool:
        if guess == self.word:
            return True

        if len(guess) != self.guess_length:
            if not raise_error:
                return False
            raise InvalidGuessLength(guess=guess, expected_length=self.guess_length)
        if guess in self._guesses:
            if not raise_error:
                return False
            raise RepeatGuess(guess)
        if guess not in self.valid_words:
            if not raise_error:
                return False
            raise WordNotFound(guess)

        return True

    def guess(self, guess: str) -> bool:
        self.validate_guess(guess, raise_error=True)
        guess_data: list[tuple[str, CharStatus]] = []

        for idx, char in enumerate(guess):
            if self.word[idx] == char:
                self._status[idx] = char, CharStatus.green
                guess_data.append((char, CharStatus.green))
            elif char in self.word:
                guess_data.append((char, CharStatus.yellow))

                for xchar, status in self._status:
                    if xchar == char and status is not CharStatus.green:
                        self._yellow_chars.add(char)
            else:
                guess_data.append((char, CharStatus.black))
                self._black_chars.add(char)

        self._guesses[guess] = guess_data

        if len(self._guesses) == self.amount_of_guesses:
            raise OutOfGuesses()

        return False
