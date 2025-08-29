__all__ = (
    "InvalidGuess",
    "InvalidGuessLength",
    "OutOfGuesses",
    "RepeatGuess",
    "WordNotFound",
    "WordleException",
)


class WordleException(Exception): ...


class InvalidGuess(WordleException):
    __slots__ = ("guess",)

    def __init__(self, msg: str, guess: str) -> None:
        super().__init__(msg)

        self.guess = guess


class InvalidGuessLength(InvalidGuess):
    __slots__ = ("expected_length",)

    def __init__(self, *, guess: str, expected_length: int) -> None:
        super().__init__(
            f"Expected a length of {expected_length} but received {len(guess)} instead.",
            guess,
        )

        self.expected_length = expected_length


class RepeatGuess(InvalidGuess):
    def __init__(self, guess: str) -> None:
        super().__init__(f"Duplicate guess of {guess!r}", guess)


class WordNotFound(InvalidGuess):
    def __init__(self, guess: str) -> None:
        super().__init__(
            f"The word {guess!r} was not found in the list of acceptable words", guess
        )


class OutOfGuesses(WordleException):
    def __init__(self) -> None:
        super().__init__("You ran out of guesses")
