from __future__ import annotations

from typing import TYPE_CHECKING, Unpack

from flogin import ExecuteResponse, Query, Result
from flogin.jsonrpc.results import ResultConstructorArgs

from .errors import CorrectGuess, OutOfGuesses
from .enums import StatusEnum
if TYPE_CHECKING:
    from .plugin import WordlePlugin


class MakeGuessResult(Result):
    plugin: WordlePlugin | None  # type: ignore

    def __init__(self, query: Query, remaining_guesses: int) -> None:
        super().__init__(
            title=f"Guess {query.text}?",
            sub=f"Remaining Guesses: {remaining_guesses}",
            icon="Images/qmark.png",
        )
        self.query = query

    async def callback(self):
        assert self.plugin
        assert self.plugin.game

        results = []

        try:
            self.plugin.game.guess(self.query.text)
        except OutOfGuesses:
            results.append(
                StartGameResult(
                    self.query,
                    title=f"You ran out of guesses, game over.",
                    sub="Click to start a new game",
                    score=10,
                )
            )
            results.append(
                Result(
                    f"The word was: {self.plugin.game.word}",
                    copy_text=self.plugin.game.word,
                    score=9,
                )
            )
            results.extend(self.plugin.game.generate_state_results())
        except CorrectGuess:
            results.append(
                StartGameResult(
                    self.query,
                    title=f"You guessed it!",
                    sub="Click to start a new game",
                    score=10,
                )
            )
            self.plugin.game = None

        if results:
            await self.plugin.api.update_results(self.query.raw_text, results)
        else:
            await self.plugin.api.change_query(f"{self.query.keyword} ", requery=True)

        return ExecuteResponse(hide=False)


class StartGameResult(Result):
    plugin: WordlePlugin | None  # type: ignore

    def __init__(self, query: Query, **kwargs: Unpack[ResultConstructorArgs]) -> None:
        self.query = query

        if "icon" not in kwargs:
            kwargs["icon"] = "Images/green_circle.png"
        super().__init__(**kwargs)

    async def callback(self):
        assert self.plugin

        self.plugin.start_new_game()
        assert self.plugin.game
        await self.plugin.api.update_results(
            self.query.raw_text, self.plugin.game.generate_state_results()
        )

        return ExecuteResponse(hide=False)

class PastGuess(Result):
    def __init__(self, guess_chars: list[tuple[str, StatusEnum]]) -> None:
        word = ""
        highlight_data = []
        for idx, charinfo in enumerate(guess_chars):
            char, status = charinfo
            word += char
            if status == StatusEnum.yellow:
                highlight_data.append(idx)

        super().__init__(word, title_highlight_data=highlight_data, sub="Yellow characters are highlighted.")