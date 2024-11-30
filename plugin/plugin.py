import logging
import random

from flogin import Plugin

from .core import WordleGame
from .handlers import (
    InvalidGuessLengthHandler,
    RepeatGuessHandler,
    StartGameHandler,
    ValidGuessHandler,
    WordNotExistHandler,
)

log = logging.getLogger(__name__)


class WordlePlugin(Plugin):
    game: WordleGame | None = None
    valid_words: list[str]

    def __init__(self) -> None:
        super().__init__()

        self.register_search_handlers(
            RepeatGuessHandler(),
            InvalidGuessLengthHandler(),
            WordNotExistHandler(),
            ValidGuessHandler(),
            StartGameHandler(),
        )

    def start_new_game(self):
        word = random.choice(self.valid_words)
        log.info(f"New game started. Word: {word}")
        self.game = WordleGame(word, self)

    async def start(self):
        with open("plugin/word_list.txt", "r", encoding="UTF-8") as f:
            self.valid_words = f.read().splitlines()
        log.info("Word List Loaded")
        return await super().start()
