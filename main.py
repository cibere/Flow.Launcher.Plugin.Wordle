import os
import sys

parent_folder_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_folder_path)
sys.path.append(os.path.join(parent_folder_path, "lib"))
sys.path.append(os.path.join(parent_folder_path, ".venv", "lib", "site-packages"))

from wordle_plugin.plugin import WordlePlugin  # noqa: E402

if __name__ == "__main__":
    WordlePlugin().run()
