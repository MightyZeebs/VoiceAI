from PyQt5.QtWidgets import QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QFrame

class JarvisWidget(QFrame):
    def __init__(self, name=None, parent=None):
        super().__init__(name, parent)
        print("Creating a JarvisWidget")
        self.chat_input = QLineEdit(self)
        self.search_button = QPushButton("Search", self)
        self.chat_field = QTextEdit(self)
        self.chat_field.setReadOnly(True) #so user cant edit
        # Add the widgets to the layout in the superclass
        self.add_extra_content([self.chat_input, self.search_button, self.chat_field])

        self.chat_layout = QVBoxLayout()
        self.chat_layout.addWidget(self.chat_input)
        self.chat_layout.addWidget(self.search_button)
        self.chat_layout.addWidget(self.chat_field)
        
        self.main_layout.insertLayout(1, self.chat_layout)
        self.main_layout.setSpacing(0)
        