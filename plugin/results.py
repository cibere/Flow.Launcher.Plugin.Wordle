from __future__ import annotations

from typing import TYPE_CHECKING, Unpack, Any, Iterable

from flogin import ExecuteResponse, Glyph, Query, Result
from flogin.jsonrpc.results import ResultConstructorArgs

from .enums import StatusEnum, DisplayBlackSettingEnum
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
                    icon="Images/app.png",
                    rounded_icon=True,
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
            kwargs["rounded_icon"] = True  # type: ignore # ResultConstructorArgs is outdated the version of flogin that this repo has pinned

        super().__init__(**kwargs)

    async def callback(self):
        assert self.plugin

        self.plugin.start_new_game()
        assert self.plugin.game

        # Flow Launcher strips the raw text, so 'update_results' won't work if the user did `wordle `.
        # so my solution is change query to `wordle`, update results, then change query to `wordle `, to control the query.

        await self.plugin.api.change_query(self.query.keyword)
        await self.plugin.api.update_results(
            self.query.keyword, self.plugin.game.generate_state_results(self.query)
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
            icon=Glyph(f"#{idx + 1}", "Calibri"),
        )

class BlackLettersResult(Result):
    plugin: WordlePlugin | None  # type: ignore

    def __init__(self, *, setting: DisplayBlackSettingEnum, blacks: Iterable[str], query: Query) -> None:
        self.query = query
        black_kwargs: dict[str, Any] = {"icon": "Images/black_circle.png", "score": 40}

        match setting:
            case DisplayBlackSettingEnum.querty:
                black_title = "qwertyuiopasdfghjklzxcvbnm"
                black_highlight_data = [x for x in range(len(black_title) + 1)]
                for char in blacks:
                    black_highlight_data.remove(black_title.index(char))
                black_kwargs.update(
                    {
                        "sub": "Characters that could still be or are in the word are highlighted.",
                        "title_highlight_data": black_highlight_data,
                    }
                )
            case DisplayBlackSettingEnum.abc:
                black_title = "abcdefghijklmnopqrstuvwxyz"
                black_highlight_data = [x for x in range(len(black_title) + 1)]
                for char in blacks:
                    black_highlight_data.remove(black_title.index(char))
                black_kwargs.update(
                    {
                        "sub": "Characters that could still be or are in the word are highlighted.",
                        "title_highlight_data": black_highlight_data,
                    }
                )
            case DisplayBlackSettingEnum.only_blacks:
                black_title = "".join(blacks)
            case other:
                raise RuntimeError(
                    f"what am i supposed to do with {other!r}? It's not in {DisplayBlackSettingEnum!r}."
                )
            
        super().__init__(black_title, **black_kwargs)
    
    async def context_menu(self):
        for enum in DisplayBlackSettingEnum:
            yield ChangeSettingsOption("black_letters_display_type", enum.value, self.query,title=f"Change to {enum.value}", icon="Images/app.png", rounded_icon=True)
    
class ChangeSettingsOption(Result):
    plugin: WordlePlugin | None  # type: ignore

    def __init__(self, setting_name: str, setting_value: Any, query: Query, **kwargs):
        self.setting_name = setting_name
        self.setting_value = setting_value
        self.query = query
        super().__init__(**kwargs)

    async def callback(self):
        assert self.plugin

        self.plugin.settings[self.setting_name] = self.setting_value

        await self.plugin.api.show_notification("Wordle", "The plugin settings have been updated.", "Images/app.png")
        await self.plugin.api.change_query(self.query.keyword, True)
        await self.plugin.api.change_query(f"{self.query.keyword} " if self.query.keyword == self.query.raw_text else self.query.raw_text, True)

        return ExecuteResponse(hide=False)