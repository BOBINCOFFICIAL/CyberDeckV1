from dataclasses import dataclass, field, asdict

@dataclass
class Point:
    x: float
    y: float
    pressure: float = 1.0

@dataclass
class Stroke:
    color: str = "#000000"
    base_width: float = 2.5
    is_eraser: bool = False
    points: list[Point] = field(default_factory=list)

    def add_point(self, x: float, y: float, pressure: float =1.0):
        self.points.append(Point(x, y, pressure))

    def to_dict(self):
        return {
            "color": self.color,
            "base_width": self.base_width,
            "is_eraser": self.is_eraser,
            "points": [asdict(point) for point in self.points],

        }

    @staticmethod
    def from_dict(d):
        s = Stroke(color=d["color"], base_width=d["base_width"], is_eraser=d.get("is_eraser", False))
        s.points = [Point(**p) for p in d["points"]]
        return s
