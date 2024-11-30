from __future__ import annotations

from typing import TYPE_CHECKING, Unpack

from flogin import ExecuteResponse, Query, Result, Glyph
from flogin.jsonrpc.results import ResultConstructorArgs

from .enums import StatusEnum
from .errors import CorrectGuess, OutOfGuesses

if TYPE_CHECKING:
    from .plugin import WordlePlugin


class MakeGuessResult(Result):
    plugin: WordlePlugin | None  # type: ignore

    def __init__(self, query: Query, remaining_guesses: int) -> None:
        super().__init__(
            title=f"Guess {query.text}?",
            sub=f"Remaining Guesses: {remaining_guesses}",
            icon="Images/qmark.png",
            score=100000,
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
                    score=100001,
                )
            )
            results.append(
                Result(
                    f"The word was: {self.plugin.game.word}",
                    copy_text=self.plugin.game.word,
                    score=100000,
                    icon="Images/app.png", rounded_icon=True
                )
            )
            self.plugin.game = None
        except CorrectGuess:
            results.append(
                StartGameResult(
                    self.query,
                    title=f"You guessed it!",
                    sub="Click to start a new game",
                    score=100000,
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
            kwargs["icon"] = "Images/app.png"
            kwargs['rounded_icon'] = True # type: ignore # ResultConstructorArgs is outdated the version of flogin that this repo has pinned
            
        super().__init__(**kwargs)

    async def callback(self):
        assert self.plugin

        self.plugin.start_new_game()
        assert self.plugin.game

        # Flow Launcher strips the raw text, so 'update_results' won't work if the user did `wordle `.
        # so my solution is change query to `wordle`, update results, then change query to `wordle `, to control the query.

        await self.plugin.api.change_query(self.query.keyword)
        await self.plugin.api.update_results(
            self.query.keyword, self.plugin.game.generate_state_results()
        )
        await self.plugin.api.change_query(f"{self.query.keyword} ")

        return ExecuteResponse(hide=False)


class PastGuess(Result):
    def __init__(self, guess_chars: list[tuple[str, StatusEnum]], idx: int) -> None:
        word = ""
        highlight_data = []
        for cidx, charinfo in enumerate(guess_chars):
            char, status = charinfo
            word += char
            if status == StatusEnum.yellow:
                highlight_data.append(cidx)

        super().__init__(
            word,
            title_highlight_data=highlight_data,
            sub="Yellow characters are highlighted.",
            score=idx,
            icon=Glyph(f"#{idx + 1}", "Calibri")
        )
