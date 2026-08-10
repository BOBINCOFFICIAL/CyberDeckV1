
import json
from stroke import Stroke


class PageManager:
    def __init__(self):
        self.pages: list[list[Stroke]] = [[]]
        self.current_index = 0

    @property
    def current_strokes(self) -> list[Stroke]:
        return self.pages[self.current_index]

    def new_page(self):
        self.pages.append([])
        self.current_index = len(self.pages) - 1

    def next_page(self) -> bool:
        if self.current_index < len(self.pages) - 1:
            self.current_index += 1
            return True
        return False

    def prev_page(self) -> bool:
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def save_current(self, strokes: list[Stroke]):
        self.pages[self.current_index] = strokes

    def to_json(self) -> str:
        return json.dumps({
            "pages": [[s.to_dict() for s in page] for page in self.pages]
        })

    def load_json(self, text: str):
        data = json.loads(text)
        self.pages = [[Stroke.from_dict(s) for s in page] for page in data["pages"]]
        self.current_index = 0

    def save_to_file(self, path: str):
        with open(path, "w") as f:
            f.write(self.to_json())

    def load_from_file(self, path: str):
        with open(path, "r") as f:
            self.load_json(f.read())