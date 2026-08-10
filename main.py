
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLabel, QFileDialog, QMessageBox,
    QColorDialog
)
from PySide6.QtGui import (
    QAction, QActionGroup, QKeySequence, QIcon, QPixmap, QColor,
    QPainter, QBrush, QPen
)
from PySide6.QtCore import Qt, QSize

from canvas import DrawingCanvas
from page_manager import PageManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Notebook (dev build)")

        self.pages = PageManager()
        self.canvas = DrawingCanvas(width=1404, height=1872)
        self.setCentralWidget(self.canvas)

        self.toolbar = None
        self._build_toolbar()
        self.resize(720, 960)

    def _build_toolbar(self):
        tb = QToolBar("Tools")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        self.addToolBar(tb)
        self.toolbar = tb

        self.current_pen_color = "#000000"
        self.pen_width = 2.5

        pen_action = QAction("Pen", self, checkable=True, checked=True)
        pen_action.triggered.connect(lambda: self.canvas.set_pen(self.current_pen_color, self.pen_width))
        eraser_action = QAction("Eraser", self, checkable=True)
        eraser_action.triggered.connect(self.canvas.set_eraser)

        mode_group = QActionGroup(self)
        mode_group.addAction(pen_action)
        mode_group.addAction(eraser_action)
        tb.addAction(pen_action)
        tb.addAction(eraser_action)
        self.pen_action = pen_action

        tb.addSeparator()
        self._build_color_palette(tb)

        tb.addSeparator()

        undo_action = QAction("Undo", self, shortcut=QKeySequence.Undo)
        undo_action.triggered.connect(self.canvas.undo)
        redo_action = QAction("Redo", self, shortcut=QKeySequence.Redo)
        redo_action.triggered.connect(self.canvas.redo)
        clear_action = QAction("Clear Page", self)
        clear_action.triggered.connect(self._confirm_clear)
        tb.addAction(undo_action)
        tb.addAction(redo_action)
        tb.addAction(clear_action)

        tb.addSeparator()

        prev_action = QAction("< Prev Page", self)
        prev_action.triggered.connect(self._prev_page)
        next_action = QAction("Next Page >", self)
        next_action.triggered.connect(self._next_page)
        tb.addAction(prev_action)
        tb.addAction(next_action)
        self.page_label = QLabel("Page 1 / 1")
        tb.addWidget(self.page_label)

        tb.addSeparator()

        save_action = QAction("Save Notebook", self, shortcut=QKeySequence.Save)
        save_action.triggered.connect(self._save_notebook)
        open_action = QAction("Open Notebook", self, shortcut=QKeySequence.Open)
        open_action.triggered.connect(self._open_notebook)
        export_action = QAction("Export Page as PNG", self)
        export_action.triggered.connect(self._export_png)
        tb.addAction(save_action)
        tb.addAction(open_action)
        tb.addAction(export_action)

    def _build_color_palette(self, tb: QToolBar):
        palette = [
            ("Black", "#000000"),
            ("Red", "#e02424"),
            ("Blue", "#1d4ed8"),
            ("Green", "#15803d"),
            ("Orange", "#ea580c"),
        ]
        self.color_group = QActionGroup(self)
        self.color_actions = {}

        for name, hex_color in palette:
            action = QAction(self._color_icon(hex_color), name, self, checkable=True)
            action.triggered.connect(lambda checked, c=hex_color: self._select_color(c))
            self.color_group.addAction(action)
            tb.addAction(action)
            self.color_actions[hex_color] = action

        self.color_actions["#000000"].setChecked(True)

        custom_action = QAction("Custom...", self)
        custom_action.triggered.connect(self._pick_custom_color)
        tb.addAction(custom_action)

    def _color_icon(self, hex_color: str) -> QIcon:
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        painter_color = QColor(hex_color)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QBrush(painter_color))
        painter.setPen(QPen(Qt.gray, 1))
        painter.drawEllipse(1, 1, 18, 18)
        painter.end()
        return QIcon(pixmap)

    def _select_color(self, hex_color: str):
        self.current_pen_color = hex_color
        self.pen_action.setChecked(True)
        self.canvas.set_pen(self.current_pen_color, self.pen_width)

    def _pick_custom_color(self):
        color = QColorDialog.getColor(QColor(self.current_pen_color), self, "Pick pen color")
        if color.isValid():
            hex_color = color.name()
            if hex_color not in self.color_actions:
                action = QAction(self._color_icon(hex_color), "Custom", self, checkable=True)
                action.triggered.connect(lambda checked, c=hex_color: self._select_color(c))
                self.color_group.addAction(action)
                self.color_actions[hex_color] = action
                self.toolbar.addAction(action)
            self.color_actions[hex_color].setChecked(True)
            self._select_color(hex_color)

    def _prev_page(self):
        self.pages.save_current(self.canvas.strokes)
        if self.pages.prev_page():
            self.canvas.load_strokes(self.pages.current_strokes)
        self._update_page_label()

    def _next_page(self):
        self.pages.save_current(self.canvas.strokes)
        if not self.pages.next_page():
            self.pages.new_page()
            self.pages.current_index = len(self.pages.pages) - 1
        self.canvas.load_strokes(self.pages.current_strokes)
        self._update_page_label()

    def _update_page_label(self):
        self.page_label.setText(f"Page {self.pages.current_index + 1} / {len(self.pages.pages)}")

    def _confirm_clear(self):
        reply = QMessageBox.question(self, "Clear page", "Clear all strokes on this page?")
        if reply == QMessageBox.Yes:
            self.canvas.clear()

    def _save_notebook(self):
        self.pages.save_current(self.canvas.strokes)
        path, _ = QFileDialog.getSaveFileName(self, "Save Notebook", "notebook.json", "JSON (*.json)")
        if path:
            self.pages.save_to_file(path)

    def _open_notebook(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Notebook", "", "JSON (*.json)")
        if path:
            self.pages.load_from_file(path)
            self.canvas.load_strokes(self.pages.current_strokes)
            self._update_page_label()

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", "page.png", "PNG (*.png)")
        if path:
            self.canvas.image.save(path)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()