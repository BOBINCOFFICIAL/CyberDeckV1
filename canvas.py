from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QImage, QPen, QColor, QPainterPath, QTabletEvent
from PySide6.QtCore import Qt, QPointF, Signal

from stroke import Stroke


class DrawingCanvas(QWidget):
    strokeFinished = Signal()

    def __init__(self, width=1404, height=1872, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StaticContents)
        self.setAttribute(Qt.WA_TabletTracking)

        self.canvas_size = (width, height)
        self.image = QImage(width, height, QImage.Format_RGB32)
        self.image.fill(Qt.white)

        self.strokes: list[Stroke] = []
        self.undo_stack: list[Stroke] = []

        self.current_stroke: Stroke | None = None
        self.pen_color = "#000000"
        self.pen_width = 2.5
        self.eraser_mode = False
        self.eraser_width = 24.0

        self.setMinimumSize(width // 2, height // 2)

    def _widget_to_image(self, pos: QPointF) -> QPointF:
        sx = self.image.width() / max(self.width(), 1)
        sy = self.image.height() / max(self.height(), 1)
        return QPointF(pos.x() * sx, pos.y() * sy)

    def tabletEvent(self, event: QTabletEvent):
        pos = self._widget_to_image(event.position())
        pressure = event.pressure()

        if event.type() == QTabletEvent.TabletPress:
            self._begin_stroke(pos, pressure)
        elif event.type() == QTabletEvent.TabletMove:
            self._extend_stroke(pos, pressure)
        elif event.type() == QTabletEvent.TabletRelease:
            self._end_stroke()

        event.accept()
        self.update()

    def mousePressEvent(self, event):
        self._begin_stroke(self._widget_to_image(event.position()), 1.0)

    def mouseMoveEvent(self, event):
        if self.current_stroke is not None:
            self._extend_stroke(self._widget_to_image(event.position()), 1.0)
            self.update()

    def mouseReleaseEvent(self, event):
        self._end_stroke()
        self.update()

    def _begin_stroke(self, pos: QPointF, pressure: float):
        self.current_stroke = Stroke(
            color=self.pen_color,
            base_width=self.eraser_width if self.eraser_mode else self.pen_width,
            is_eraser=self.eraser_mode,
        )
        self.current_stroke.add_point(pos.x(), pos.y(), pressure)
        self.undo_stack.clear()

    def _extend_stroke(self, pos: QPointF, pressure: float):
        if self.current_stroke is None:
            return
        self.current_stroke.add_point(pos.x(), pos.y(), pressure)
        self._render_stroke_segment(self.current_stroke)

    def _end_stroke(self):
        if self.current_stroke and len(self.current_stroke.points) > 0:
            self.strokes.append(self.current_stroke)
            self.strokeFinished.emit()
        self.current_stroke = None

    def _render_stroke_segment(self, stroke: Stroke):
        if len(stroke.points) < 2:
            return
        p1, p2 = stroke.points[-2], stroke.points[-1]

        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if stroke.is_eraser:
            pen = QPen(Qt.white, stroke.base_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            width = stroke.base_width * (0.5 + p2.pressure)
            pen = QPen(QColor(stroke.color), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        painter.setPen(pen)
        painter.drawLine(QPointF(p1.x, p1.y), QPointF(p2.x, p2.y))
        painter.end()

    def _full_redraw(self):
        self.image.fill(Qt.white)
        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        for stroke in self.strokes:
            path = QPainterPath()
            if not stroke.points:
                continue
            path.moveTo(stroke.points[0].x, stroke.points[0].y)
            for pt in stroke.points[1:]:
                path.lineTo(pt.x, pt.y)
            color = Qt.white if stroke.is_eraser else QColor(stroke.color)
            width = stroke.base_width if stroke.is_eraser else stroke.base_width * 0.9
            pen = QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(path)
        painter.end()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        target = self.rect()
        painter.drawImage(target, self.image, self.image.rect())

    def set_pen(self, color: str, width: float):
        self.eraser_mode = False
        self.pen_color = color
        self.pen_width = width

    def set_eraser(self):
        self.eraser_mode = True

    def undo(self):
        if self.strokes:
            self.undo_stack.append(self.strokes.pop())
            self._full_redraw()

    def redo(self):
        if self.undo_stack:
            self.strokes.append(self.undo_stack.pop())
            self._full_redraw()

    def clear(self):
        self.strokes.clear()
        self.undo_stack.clear()
        self._full_redraw()

    def load_strokes(self, strokes: list[Stroke]):
        self.strokes = strokes
        self.undo_stack.clear()
        self._full_redraw()