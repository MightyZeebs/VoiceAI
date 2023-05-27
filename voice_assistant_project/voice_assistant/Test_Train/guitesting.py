import sys
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QIcon, QDrag, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout, QFrame, QPushButton, QToolBar, QSizePolicy, QToolButton, QLabel

class DraggableButton(QPushButton):
    def __init__(self, title, parent):
        super().__init__(title, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mimedata = QMimeData()

        mimedata.setText(self.text())
        drag.setMimeData(mimedata)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())

        drag.exec_(Qt.MoveAction)

class DroppableFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)
        self.closeButton = QToolButton(self)
        self.closeButton.setText("X")
        self.closeButton.setFixedSize(15, 15)
        self.closeButton.setVisible(False)
        self.closeButton.clicked.connect(self.clear)
        self.closeButton.setStyleSheet('background-color: white; border: none')

    def resizeEvent(self, event):
        self.closeButton.move(self.width() - self.closeButton.width(), 0)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text()
        sender = event.source()

        if text == "DraggableFrame":
            while sender.layout.count() > 0:
                item = sender.layout.takeAt(0).widget()
                self.layout.addWidget(item)
            sender.setParent(None)
            sender.deleteLater()
            
        elif isinstance(sender, DraggableButton):
            previous_dock = sender.parent()
            if isinstance(previous_dock, DroppableFrame):
                previous_dock.removeButton(sender)
            self.closeButton.setVisible(True)

            button = DraggableButton(text, self)
            button.setStyleSheet("background-color: red;")
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            self.layout.addWidget(button)
            self.closeButton.raise_()
            self.closeButton.setVisible(True)

    def removeButton(self, button):
        if self.layout is not None:
            self.layout.removeWidget(button)
            button.setParent(None)
            button.deleteLater()
            self.closeButton.setVisible(False)

    def clear(self):
        # Clear all widgets except the close button
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget != self.closeButton:
                self.layout.removeWidget(widget)
                widget.setParent(None)
                widget.deleteLater()
        # Check if there's a visible widget left
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget and widget.isVisible():
                return
        self.closeButton.setVisible(False)  # Hide the close button if no visible widget left

class DraggableFrame(DroppableFrame):
    def __init__(self):
        super().__init__()

        self.setFixedSize(200, 200)  # set fixed size for simplicity
        self.setStyleSheet("background-color: lightgreen;")  # change color to differentiate

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mimedata = QMimeData()

        mimedata.setText("DraggableFrame")  # mark this as draggable frame
        drag.setMimeData(mimedata)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())

        drag.exec_(Qt.MoveAction)

class ResizeHandle(QPushButton):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mimedata = QMimeData()

        mimedata.setText("ResizeHandle")  # mark this as Resize Handle
        drag.setMimeData(mimedata)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())

        drag.exec_(Qt.MoveAction)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dockable Window GUI")
        self.setGeometry(100, 100, 800, 600)
        self.create_widgets()
        self.create_tool_bar()

    def create_widgets(self):
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        main_layout.addLayout(grid_layout)

        for i in range(12):
            dock_area = DroppableFrame()
            dock_area.setFrameStyle(QFrame.Box)
            dock_area.setLineWidth(2)
            dock_area.setStyleSheet("background-color: darkgray;")
            grid_layout.addWidget(dock_area, i // 4, i % 4)

    def create_tool_bar(self):
        self.tool_bar = QToolBar()
        self.addToolBar(Qt.TopToolBarArea, self.tool_bar)  # Changed from LeftToolBarArea to TopToolBarArea

        button1 = DraggableButton("1", self)
        button1.setStyleSheet("background-color: red;")
        self.tool_bar.addWidget(QLabel("Button 1"))  # Add a label to describe the button
        self.tool_bar.addWidget(button1)

        self.tab_widget = QWidget(self)
        self.tab_widget.setFixedSize(30, 100)
        self.tab_widget.move(0, 0)
        self.tab_widget.setStyleSheet("background-color: lightgray;")

        toggle_button = QPushButton(self.tab_widget)
        toggle_button.setFixedSize(20, 20)
        toggle_button.move(5, 40)
        toggle_button.setText(">")
        toggle_button.clicked.connect(self.toggle_tool_bar)
        self.tool_bar.setVisible(False)
        self.tool_bar.actionTriggered.connect(self.adjust_tab_position)

    def adjust_tab_position(self, action):
        if action.isVisible():
            self.tab_widget.move(self.tool_bar.width(), 0)
        else:
            self.tab_widget.move(0, 0)

    def toggle_tool_bar(self):
        if self.tool_bar.isVisible():
            self.tool_bar.setVisible(False)
            self.tab_widget.move(0, 0)
        else:
            self.tool_bar.setVisible(True)
            self.tab_widget.move(self.tool_bar.width(), 0)

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
    """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
