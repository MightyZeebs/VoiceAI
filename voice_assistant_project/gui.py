import sys
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame, QPushButton, QToolBar, QSizePolicy, QSpacerItem
from PyQt5.QtWidgets import QMenu, QMdiSubWindow, QMdiArea
from CellWidget import CellWidget
from jarvis import JarvisWidget
from voice_assistant.assistant import VoiceAssistant
from voice_assistant.speech import synthesize_speech, play_speech_threaded
from voice_assistant.openai_integration import handle_question

class HoverButton(QPushButton):
    add_cell_signal = pyqtSignal(int)  # This signal sends an integer

    def __init__(self, *args, **kwargs):
        super(HoverButton, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
        # Set the text of the button
        self.setText("Add Cell")
        # Optionally, set an icon
        # self.setIcon(QIcon("path_to_icon.png"))
        # Set the size of the button to fit the text and the icon
        self.setFixedSize(100, 100) # Adjust the size based on your needs
        self.jarvis_active = False
        self.menu = QMenu(self)
        for i in range(1, 4):  # For 1, 2, and 3
            action = self.menu.addAction(str(i))
            action.triggered.connect(lambda checked, i=i: self.add_cell_signal.emit(i))

    def enterEvent(self, event):
        self.menu.exec_(self.mapToGlobal(self.rect().bottomLeft()))

class DraggableButton(QPushButton):
    drag_jarvis_signal = pyqtSignal()

    def __init__(self, name, *args, **kwargs):
        super(DraggableButton, self).__init__(*args, **kwargs)
        self.name = name
        self.setText(self.name)
        self.setFixedSize(100, 100)
        self.drag_start_position = None  # Initialize drag_start_position

    def mousePressEvent(self, e):
        super().mousePressEvent(e)  # ensure normal button behavior
        if e.button() == Qt.LeftButton:
            self.drag_start_position = e.pos()
            if self.text() == "Jarvis":
                self.setStyleSheet("background-color: red;")  # highlight button
                self.drag_jarvis_signal.emit()  # emit signal even if button is just clicked


    def mouseMoveEvent(self, e):
        if not (e.buttons() & Qt.LeftButton):
            return
        if self.drag_start_position is not None and \
            (e.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mimedata = QMimeData()

        # Add name to the dragged data
        mimedata.setText(self.name)
        drag.setMimeData(mimedata)
        if self.name == "Jarvis":
            self.drag_jarvis_signal.emit()
        drag.exec_(Qt.MoveAction)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Resizable Cells Demo")
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.voice_assistant = None
        self.toolbar = QToolBar()
        self.toolbar.setOrientation(Qt.Vertical)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        main_layout.addWidget(self.toolbar)
        self.jarvis_active = False
        self.add_jarvis_button = DraggableButton("Jarvis", self)
        self.add_jarvis_button.drag_jarvis_signal.connect(self.add_jarvis_widget)
        self.toolbar.addWidget(self.add_jarvis_button)
        self.add_cell_button = HoverButton("Add Cell", self)
        self.toolbar.addWidget(self.add_cell_button)
        self.add_cell_button.add_cell_signal.connect(self.add_cell)
        self.splitter = QSplitter(Qt.Horizontal, main_widget)
        main_layout.addWidget(self.splitter)

        for _ in range(3):  # Add 3 rows
            h_splitter = QSplitter(Qt.Vertical)
            self.splitter.addWidget(h_splitter)

            for _ in range(3):  # Add 3 columns
                cell_widget = CellWidget(parent=h_splitter)
                h_splitter.addWidget(cell_widget)

    def add_cell(self, column):
        if 0 < column <= self.splitter.count():
            target_splitter = self.splitter.widget(column - 1)
            cell_widget = CellWidget("Cell")
            target_splitter.addWidget(cell_widget)
    
    def set_voice_assistant(self, voice_assistant):
        self.voice_assistant = voice_assistant
        voice_assistant.main_window = self

    def add_jarvis_widget(self):
        print("add_jarvis_widget triggered")
        self.jarvis_active = True
        self.jarvis_widget = JarvisWidget()   # create an instance of JarvisWidget
        self.jarvis_widget.set_voice_assistant(self.voice_assistant)  # call the method on the instance
        self.add_jarvis_button.setStyleSheet("background-color: red;")  # highlight button

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def find_drop_target(self, widget, pos):
        child = widget.childAt(widget.mapFromGlobal(pos))
        if child is None:
            return widget
        else:
            return self.find_drop_target(child, pos)

    def dropEvent(self, event):
        print("MainWindow dropEvent: ", event.mimeData().text())
        if event.mimeData().hasText():
            global_pos = event.globalPos()
            target_widget = self.find_drop_target(self, global_pos)
            if isinstance(target_widget, CellWidget):
                if event.mimeData().text() == "Jarvis":
                    target_widget.delete_self()  # Delete the existing CellWidget
                    # Create and insert a new JarvisWidget
                    jarvis_widget = JarvisWidget(target_widget.parent())
                    target_widget.parent().addWidget(jarvis_widget)


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