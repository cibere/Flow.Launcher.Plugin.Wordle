class WordleException(Exception): ...


class CorrectGuess(WordleException):
    def __init__(self) -> None:
        super().__init__("You guessed it!")


class InvalidGuess(WordleException): ...


class RepeatGuess(InvalidGuess):
    def __init__(self, word: str) -> None:
        super().__init__(f"Repeat guess of {word!r}")


class OutOfGuesses(WordleException):
    def __init__(self) -> None:
        super().__init__("Out of guesses, you lose.")
