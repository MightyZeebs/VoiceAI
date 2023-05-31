from PyQt5.QtWidgets import QVBoxLayout, QLineEdit, QPushButton, QFrame, QCheckBox, QListView, QStyledItemDelegate
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainter, QColor
from PyQt5.QtCore import pyqtSlot, Qt, QSize


class BubbleDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(BubbleDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        if not index.isValid():
            return

        text = index.data(Qt.DisplayRole)
        if text:
            text_rect = option.rect.adjusted(10, 5, -10, -5)

            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#3daee9"))
            painter.drawRoundedRect(text_rect, 10, 10)

            painter.setPen(QColor("#2b2b2b"))
            painter.drawText(text_rect, Qt.AlignCenter, text)

            painter.restore()

    def sizeHint(self, option, index):
        return QSize(100, 30)


class JarvisWidget(QFrame):
    def __init__(self, parent=None):
        super(JarvisWidget, self).__init__(parent)
        print("Creating a JarvisWidget")
        self.chat_input = QLineEdit(self)
        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.process_query)
        self.chat_list_view = QListView(self)
        self.chat_list_model = QStandardItemModel(self.chat_list_view)
        self.chat_list_view.setModel(self.chat_list_model)
        self.chat_list_view.setItemDelegate(BubbleDelegate())

        self.web_search_checkbox = QCheckBox("Force web search", self)

        self.chat_layout = QVBoxLayout()
        self.setLayout(self.chat_layout)

        self.add_extra_content([self.chat_input, self.search_button, self.chat_list_view, self.web_search_checkbox])

        self.setStyleSheet("""
            JarvisWidget {
                background-color: #31363b;
                color: #eff0f1;
            }
            QLineEdit {
                background-color: #45494e;
                color: #eff0f1;
                border: none;
            }
            QListView {
                background-color: transparent;
                border: none;
            }
        """)

    def set_voice_assistant(self, voice_assistant):
        self.voice_assistant = voice_assistant
        voice_assistant.jarvis_widget = self

    def add_extra_content(self, widgets):
        for widget in widgets:
            self.layout().addWidget(widget)

    @pyqtSlot()
    def process_query(self):
        query = self.chat_input.text()
        self.chat_input.clear()
        if query:
            if self.web_search_checkbox.isChecked():
                query = "web search needed" + query
            assistant_response = self.voice_assistant.handle_transcript(query)

    def display_message(self, message):
        item = QStandardItem(message)
        self.chat_list_model.appendRow(item)
        self.chat_list_view.scrollToBottom()
