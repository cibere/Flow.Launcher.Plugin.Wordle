from __future__ import annotations

import random
from typing import TYPE_CHECKING, TypedDict, Unpack

from flogin import (
    ExecuteResponse,
    Glyph,
    ProgressBar,
    Query,
    ResultPreview,
)
from flogin import (
    Result as _Res,
)

from wordle import CharStatus, OutOfGuesses

from .enums import Icon

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .plugin import WordlePlugin  # noqa: F401


class ResultOptions(TypedDict, total=False):
    title: str | None
    sub: str | None
    icon: Icon
    title_highlight_data: Iterable[int] | None
    title_tooltip: str | None
    sub_tooltip: str | None
    copy_text: str | None
    score: int | None
    preview: ResultPreview | None
    progress_bar: ProgressBar | None
    rounded_icon: bool | None
    glyph: Glyph | None


class Result(_Res["WordlePlugin"]):
    def __init__(
        self,
        title: str | None = None,
        sub: str | None = None,
        icon: Icon = Icon.app,
        title_highlight_data: Iterable[int] | None = None,
        title_tooltip: str | None = None,
        sub_tooltip: str | None = None,
        copy_text: str | None = None,
        score: int | None = None,
        preview: ResultPreview | None = None,
        progress_bar: ProgressBar | None = None,
        rounded_icon: bool | None = None,
        glyph: Glyph | None = None,
    ) -> None:
        super().__init__(
            title=title,
            sub=sub,
            icon=icon.value,
            title_highlight_data=title_highlight_data,
            title_tooltip=title_tooltip,
            sub_tooltip=sub_tooltip,
            copy_text=copy_text,
            score=(score * 10000) if score else score,
            auto_complete_text="".join(random.choices("qweiopasdfghjklzxcvbnm", k=10)),
            preview=preview,
            progress_bar=progress_bar,
            rounded_icon=True if icon is Icon.app else rounded_icon,
            glyph=glyph,
        )


class MakeGuessResult(Result):
    def __init__(self, query: Query[None], remaining_guesses: int) -> None:
        super().__init__(
            title=f"Guess {query.text}?",
            sub=f"Remaining Guesses: {remaining_guesses}",
            icon=Icon.qmark,
            score=100,
        )

        self.query = query

    async def callback(self) -> ExecuteResponse:
        assert self.plugin
        assert self.plugin.game

        results: list[Result] = []
        correct = False

        try:
            correct = self.plugin.game.guess(self.query.text)
        except OutOfGuesses:
            results.append(
                StartGameResult(
                    self.query,
                    title="You ran out of guesses, game over.",
                    sub="Click to start a new game",
                    score=100001,
                )
            )
            results.append(
                Result(
                    f"The word was: {self.plugin.game.word}",
                    copy_text=self.plugin.game.word,
                    score=100000,
                )
            )
            self.plugin.game = None

        if correct:
            results.append(
                StartGameResult(
                    self.query,
                    title="You guessed it!",
                    sub="Click to start a new game",
                    score=100000,
                )
            )
            self.plugin.game = None

        if results:
            await self.plugin.api.update_results(self.query.raw_text, results)  # pyright: ignore[reportArgumentType]
        else:
            await self.plugin.api.change_query(f"{self.query.keyword} ", requery=True)

        return ExecuteResponse(hide=False)


class StartGameResult(Result):
    def __init__(self, query: Query[None], **kwargs: Unpack[ResultOptions]) -> None:
        super().__init__(**kwargs)

        self.query = query

    async def callback(self) -> ExecuteResponse:
        assert self.plugin

        self.plugin.start_new_game()
        assert self.plugin.game

        # Flow Launcher strips the raw text, so 'update_results' won't work if the user did `wordle `.
        # so my solution is change query to `wordle`, update results, then change query to `wordle `, to control the query.

        await self.plugin.api.change_query(self.query.keyword)
        await self.plugin.api.update_results(
            self.query.keyword,
            self.plugin.gen_state_results(),  # pyright: ignore[reportArgumentType]
        )
        # await self.plugin.api.change_query(f"{self.query.keyword} ")

        return ExecuteResponse(hide=False)


class PastGuess(Result):
    def __init__(self, guess_chars: list[tuple[str, CharStatus]], idx: int) -> None:
        word = ""
        highlight_data: list[int] = []
        for cidx, charinfo in enumerate(guess_chars):
            char, status = charinfo
            word += char
            if status == CharStatus.yellow:
                highlight_data.append(cidx)

        super().__init__(
            word,
            title_highlight_data=highlight_data,
            sub="Yellow characters are highlighted.",
            score=idx,
            glyph=Glyph(f"#{idx + 1}", "Calibri"),
        )
