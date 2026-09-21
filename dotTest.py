
import sys
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QColor, QKeyEvent
from PySide6.QtCore import Qt, QPointF


class DotTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Touch Test")
        self.setStyleSheet("background-color: black;")
        self.dots: list[QPointF] = []
        self.dot_radius = 18

        # Fullscreen, black background, no window chrome getting in the way.
        self.showFullScreen()

    def mousePressEvent(self, event):
        self.dots.append(event.position())
        self.update()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.close()
        elif event.key() == Qt.Key_C:
            # 'c' clears all dots, handy once the screen fills up
            self.dots.clear()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QColor("#a855f7"))  # purple
        painter.setPen(Qt.NoPen)
        for pos in self.dots:
            painter.drawEllipse(pos, self.dot_radius, self.dot_radius)


def main():
    app = QApplication(sys.argv)
    win = DotTestWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()