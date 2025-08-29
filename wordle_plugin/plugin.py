from __future__ import annotations

from typing import Any

from flogin import Plugin

from wordle import WordleGame

from .enums import BlackDisplay, Icon
from .handlers import GuessHandler, StartGameHandler
from .results import PastGuess, Result
from .settings import WordleSettings


class WordlePlugin(Plugin[WordleSettings]):
    game: WordleGame | None = None

    def __init__(self) -> None:
        super().__init__()

        self.register_search_handlers(
            GuessHandler(),
            StartGameHandler(),
        )

    def start_new_game(self) -> None:
        self.game = WordleGame()

    def gen_state_results(self) -> list[Result]:
        assert self.game
        black_kwargs: dict[str, Any] = {"icon": Icon.black_circle, "score": 40}

        match BlackDisplay(self.settings.black_letters_display_type):
            case BlackDisplay.querty:
                black_title = "qwertyuiopasdfghjklzxcvbnm"
                black_highlight_data = list(range(len(black_title) + 1))
                for char in self.game.black_chars:
                    black_highlight_data.remove(black_title.index(char))
                black_kwargs.update(
                    {
                        "sub": "Characters that could still be or are in the word are highlighted.",
                        "title_highlight_data": black_highlight_data,
                    }
                )
            case BlackDisplay.abc:
                black_title = "abcdefghijklmnopqrstuvwxyz"
                black_highlight_data = list(range(len(black_title) + 1))
                for char in self.game.black_chars:
                    black_highlight_data.remove(black_title.index(char))
                black_kwargs.update(
                    {
                        "sub": "Characters that could still be or are in the word are highlighted.",
                        "title_highlight_data": black_highlight_data,
                    }
                )
            case BlackDisplay.only_blacks:
                black_title = "".join(self.game.black_chars)

        return [
            Result(
                " ".join(self.game.status("_")),
                icon=Icon.green_circle,
                score=50,
            ),
            Result(black_title, **black_kwargs),
            *[
                PastGuess(guess, idx)
                for idx, guess in enumerate(self.game.past_guesses)
            ],
        ]
