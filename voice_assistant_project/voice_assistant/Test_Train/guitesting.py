import sys
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame, QPushButton, QToolBar, QSizePolicy
from PyQt5.QtWidgets import QMenu

class HoverButton(QPushButton):
    add_cell_signal = pyqtSignal(int)  # This signal sends an integer

    def __init__(self, *args, **kwargs):
        super(HoverButton, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)

        self.menu = QMenu(self)
        for i in range(1, 4):  # For 1, 2, and 3
            action = self.menu.addAction(str(i))
            action.triggered.connect(lambda checked, i=i: self.add_cell_signal.emit(i))

    def enterEvent(self, event):
        self.menu.exec_(self.mapToGlobal(self.rect().bottomLeft()))


class DraggableButton(QPushButton):
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_start_position = e.pos()

    def mouseMoveEvent(self, e):
        if not (e.buttons() & Qt.LeftButton):
            return
        if (e.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mimedata = QMimeData()
        mimedata.setText(self.text())
        drag.setMimeData(mimedata)
        drag.exec_(Qt.MoveAction)


class CellWidget(QFrame):
    def __init__(self, parent=None):
        super(CellWidget, self).__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.button = QPushButton("Cell", self)
        layout.addWidget(self.button)

        self.delete_button = QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.delete_self)
        layout.addWidget(self.delete_button)

    def delete_self(self):
        self.setParent(None)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Resizable Cells Demo")
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = QToolBar()
        self.toolbar.setOrientation(Qt.Vertical)
        main_layout.addWidget(self.toolbar)

        # Create the HoverButton here
        self.add_cell_button = HoverButton("Add Cell", self)
        self.toolbar.addWidget(self.add_cell_button)
        self.add_cell_button.add_cell_signal.connect(self.add_cell) 

        self.splitter = QSplitter(Qt.Horizontal, main_widget)
        main_layout.addWidget(self.splitter)

        for _ in range(3):  # Add 3 rows
            h_splitter = QSplitter(Qt.Vertical)
            self.splitter.addWidget(h_splitter)

            for _ in range(3):  # Add 3 columns
                cell_widget = CellWidget(h_splitter)
                h_splitter.addWidget(cell_widget)

    def add_cell(self, column):
        if 0 < column <= self.splitter.count():
            target_splitter = self.splitter.widget(column - 1)
            cell_widget = CellWidget()
            target_splitter.addWidget(cell_widget)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def find_drop_target(self, widget, pos):
        child = widget.childAt(widget.mapFromGlobal(pos))
        if child is None:
            return widget
        else:
            return self.find_drop_target(child, pos)

    def dropEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text() == "Add Cell":
            global_pos = event.globalPos()
            target_widget = self.find_drop_target(self, global_pos)
            if isinstance(target_widget, QSplitter):
                cell_widget = CellWidget()
                target_widget.addWidget(cell_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
        }
        QPushButton {
            background-color: #31363b;
            color: #eff0f1;
            border: none;
        }
        QPushButton:hover {
            background-color: #3daee9;
            color: #2b2b2b;
        }
    QPushButton:hover {
            background-color: #3daee9;
            color: #2b2b2b;
        }
        QMenu {
            background-color: #ffffff;  /* Changing the background color of the QMenu */
            color: #000000;             /* Changing the text color of the QMenu */
        }
        QMenu::item:selected {
            background-color: #ff0000;  /* Changing the background color of the selected QMenu item */
        }
    """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())