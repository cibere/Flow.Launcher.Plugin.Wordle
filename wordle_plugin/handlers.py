from __future__ import annotations

from typing import TYPE_CHECKING

from flogin import Query, SearchHandler

from wordle import InvalidGuessLength, RepeatGuess, WordNotFound

from .enums import Icon
from .results import MakeGuessResult, Result, StartGameResult

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from .plugin import WordlePlugin  # noqa: F401


class BaseHandler(SearchHandler["WordlePlugin"]):
    pass


class GuessHandler(BaseHandler):
    def condition(self, query: Query[None]) -> bool:
        return self.plugin is not None and self.plugin.game is not None

    async def callback(self, query: Query[None]) -> AsyncIterator[Result]:
        assert self.plugin
        assert self.plugin.game

        try:
            self.plugin.game.validate_guess(query.text, raise_error=True)
        except InvalidGuessLength:
            chars = len(query.text)
            diff = 5 - chars
            is_pos = abs(diff) == diff

            yield Result(
                "Invalid Guess",
                sub=f"Your guess is {abs(diff)} characters too {'short' if is_pos else 'long'}. Remaining Guesses: {self.plugin.game.remaining_guesses}",
                score=100,
                icon=Icon.error,
            )
        except RepeatGuess:
            yield Result(
                "Invalid Guess",
                sub=f"You already guessed {query.text}. Remaining Guesses: {self.plugin.game.remaining_guesses}",
                score=100,
                icon=Icon.error,
            )
        except WordNotFound:
            yield Result(
                "Invalid Word",
                score=100,
                icon=Icon.error,
                sub=f"Remaining Guesses: {self.plugin.game.remaining_guesses}",
            )
        else:
            yield MakeGuessResult(query, self.plugin.game.remaining_guesses)

        for res in self.plugin.gen_state_results():
            yield res


class StartGameHandler(BaseHandler):
    def condition(self, query: Query[None]) -> bool:
        return self.plugin is not None and self.plugin.game is None

    async def callback(self, query: Query[None]) -> Result:
        return StartGameResult(
            query, title="Start a game?", sub="Click to start a new game"
        )
