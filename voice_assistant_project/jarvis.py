from PyQt5.QtWidgets import QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QFrame, QCheckBox
from PyQt5.QtCore import pyqtSlot


class JarvisWidget(QFrame):
    def __init__(self, parent=None):
        super(JarvisWidget, self).__init__(parent)
        print("Creating a JarvisWidget")
        self.chat_input = QLineEdit(self)
        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.process_query)  # Connect the button click to process_query method
        self.chat_field = QTextEdit(self)
        self.chat_field.setReadOnly(True) #so user cant edit
        self.web_search_checkbox = QCheckBox("Force web search", self)

        # Create the layout and set it for this widget
        self.chat_layout = QVBoxLayout()
        self.setLayout(self.chat_layout)

        # Now that the layout is set, we can add widgets to it
        self.add_extra_content([self.chat_input, self.search_button, self.chat_field, self.web_search_checkbox])

    def set_voice_assistant(self, voice_assistant):
        self.voice_assistant = voice_assistant

    def add_extra_content(self, widgets):
        for widget in widgets:
            self.layout().addWidget(widget)

    @pyqtSlot()
    def process_query(self):
        query = self.chat_input.text()  # Get the user's input from the QLineEdit
        self.chat_input.clear()  # Clear the user's input
        if query:
            if self.web_search_checkbox.isChecked():
                query = "web search needed" + query
            self.voice_assistant.handle_transcript(query)
            assistant_response = "Understood."
            # Update the chat field
            self.chat_field.append("User: " + query)
            self.chat_field.append("Assistant: " + assistant_response)