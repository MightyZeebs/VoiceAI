import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QSizePolicy, QMdiSubWindow
from jarvis import JarvisWidget

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
        self.delete_button.setStyleSheet("""
            background-color: #31363b;
            border-radius: 12px;
        """)


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

        self.setStyleSheet("""
            CellWidget {
                background-color: #31363b;
                color: #eff0f1;
                border-radius: 15px;
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

    def add_extra_content(self, widgets):
        for widget in widgets:
            self.extra_content_layout.addWidget(widget)

    def delete_self(self):
        # If the cell has a widget, clear it
        if self.has_widget:
            # Iterate over all widgets in the layout and remove them
            for i in reversed(range(self.main_layout.count())): 
                widget = self.main_layout.itemAt(i).widget()
                if widget is not None:  # if widget exists
                    widget.deleteLater()  # delete the widget

            # Reset cell to default state
            self.delete_button.clicked.connect(self.delete_self)
            self.delete_button.setFixedSize(25, 25)

            top_layout = QHBoxLayout()
            top_layout.setContentsMargins(0, 2, 2, 0)  # right & top margin is set to 2
            top_layout.addStretch()
            top_layout.addWidget(self.delete_button)

            self.main_layout.addLayout(top_layout)

            self.button = QPushButton(self.name if self.name else "Cell")
            self.button.setParent(self)
            self.main_layout.addWidget(self.button, alignment=Qt.AlignCenter)
            self.has_widget = False  # Reset the has_widget flag
        else:
            # If the cell is empty, delete it
            parent = self.parent()
            # Remove the cell widget from its parent splitter
            index = parent.indexOf(self)
            parent.widget(index).setParent(None)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            if event.mimeData().text() == "Jarvis": # previously it was "AI Jarvis"
                event.ignore()  # this will propagate the event to the parent widget
            else:
                event.accept()

    def mousePressEvent(self, e):
        super().mousePressEvent(e)  # ensure normal click behavior
        main_window = self.window()
        if e.button() == Qt.LeftButton and hasattr(main_window, 'jarvis_active') and main_window.jarvis_active:
            parent = self.parent()
            # Instead of deleting self, hide the button and delete button
            self.button.hide()

            jarvis_widget = JarvisWidget(self)  # The parent of JarvisWidget is the CellWidget itself
            jarvis_widget.set_voice_assistant(main_window.voice_assistant)  # Set the voice assistant for the widget
            self.main_layout.addWidget(jarvis_widget)  # Add JarvisWidget to the main layout of CellWidget
            self.has_widget = True  # Set the has_widget flag

            main_window.jarvis_active = False  # reset flag
            main_window.add_jarvis_button.setStyleSheet("")  # unhighlight button



    def dropEvent(self, event):
        print("CellWidget dropEvent: ", event.mimeData().text())
        text = event.mimeData().text().split()
        if len(text) >= 1:
            self.parent().dropEvent(event)
        else:
            print("Dropped data is not as expected")