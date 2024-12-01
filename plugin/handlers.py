from __future__ import annotations

from typing import TYPE_CHECKING

from flogin import Query, Result, SearchHandler

from .results import MakeGuessResult, StartGameResult

if TYPE_CHECKING:
    from .plugin import WordlePlugin


class BaseHandler(SearchHandler):
    def __init__(self) -> None:
        self.plugin: WordlePlugin | None = None  # type: ignore


class ValidGuessHandler(BaseHandler):
    def condition(self, query: Query) -> bool:
        return (
            self.plugin is not None
            and self.plugin.game is not None
            and len(query.text) == 5
        )

    async def callback(self, query: Query):
        assert self.plugin
        assert self.plugin.game

        return [
            MakeGuessResult(query, self.plugin.game.remaining_guesses)
        ] + self.plugin.game.generate_state_results(query)


class RepeatGuessHandler(BaseHandler):
    def condition(self, query: Query) -> bool:
        return (
            self.plugin is not None
            and self.plugin.game is not None
            and len(query.text) == 5
            and query.text in self.plugin.game.guesses
        )

    async def callback(self, query: Query):
        assert self.plugin
        assert self.plugin.game

        return [
            Result(
                f"Invalid Guess",
                sub=f"You already guessed {query.text}. Remaining Guesses: {self.plugin.game.remaining_guesses}",
                score=100,
                icon="Images/error.png",
            )
        ] + self.plugin.game.generate_state_results(query)


class InvalidGuessLengthHandler(BaseHandler):
    def condition(self, query: Query) -> bool:
        return (
            self.plugin is not None
            and self.plugin.game is not None
            and len(query.text) != 5
        )

    async def callback(self, query: Query):
        assert self.plugin
        assert self.plugin.game

        chars = len(query.text)
        diff = 5 - chars
        is_pos = abs(diff) == diff
        return [
            Result(
                f"Invalid Guess",
                sub=f"Your guess is {abs(diff)} characters too {'short' if is_pos else 'long'}. Remaining Guesses: {self.plugin.game.remaining_guesses}",
                score=100,
                icon="Images/error.png",
            )
        ] + self.plugin.game.generate_state_results(query)


class WordNotExistHandler(BaseHandler):
    def condition(self, query: Query) -> bool:
        return (
            self.plugin is not None
            and self.plugin.game is not None
            and query.text not in self.plugin.valid_words
        )

    async def callback(self, query: Query):
        assert self.plugin
        assert self.plugin.game

        return [
            Result(
                f"Invalid Word",
                score=100,
                icon="Images/error.png",
                sub=f"Remaining Guesses: {self.plugin.game.remaining_guesses}",
            )
        ] + self.plugin.game.generate_state_results(query)


class StartGameHandler(BaseHandler):
    def condition(self, query: Query) -> bool:
        return self.plugin is not None and self.plugin.game is None

    async def callback(self, query: Query):
        return StartGameResult(
            query, title=f"Start a game?", sub=f"Click to start a new game"
        )
