import os
import sys

parent_folder_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_folder_path)
sys.path.append(os.path.join(parent_folder_path, "lib"))

from plugin.plugin import WordlePlugin

if __name__ == "__main__":
    WordlePlugin().run()
