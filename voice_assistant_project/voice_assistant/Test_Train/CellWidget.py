import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QSizePolicy

class CellWidget(QFrame):
    def __init__(self, name=None, parent=None):
        super(CellWidget, self).__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.has_widget = False
        self.name = name
        self.button = QPushButton(self.name if self.name else "Cell")
        self.button.setParent(self)

        self.delete_button = QPushButton("X", self)
        self.delete_button.clicked.connect(self.delete_self)
        self.delete_button.setFixedSize(25, 25)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 2, 2, 0)  # right & top margin is set to 2
        top_layout.addStretch()
        top_layout.addWidget(self.delete_button)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addLayout(top_layout)
        self.main_layout.addWidget(self.button, alignment=Qt.AlignCenter)
        self.setAcceptDrops(True)  # this is necessary to accept drops
        self.extra_content_layout = QVBoxLayout()
        self.main_layout.insertLayout(1, self.extra_content_layout)

    def add_extra_content(self, widgets):
        for widget in widgets:
            self.extra_content_layout.addWidget(widget)

    def delete_self(self):
        if self.has_widget:
            # If the cell has a widget, clear it
            self.has_widget = False
            self.button.setText("Cell")
        else:
            # If the cell is empty, delete it
            self.setParent(None)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            if event.mimeData().text() == "Jarvis": # previously it was "AI Jarvis"
                event.ignore()  # this will propagate the event to the parent widget
            else:
                event.accept()


    def dropEvent(self, event):
        print("CellWidget dropEvent: ", event.mimeData().text())
        text = event.mimeData().text().split()
        if len(text) >= 1:
            self.parent().dropEvent(event)
        else:
            print("Dropped data is not as expected")