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

            # Set the color according to the sender
            if text.startswith("User: "):
                painter.setBrush(QColor("#3daee9"))
            else:
                painter.setBrush(QColor("#ee3d3d"))

            painter.drawRoundedRect(text_rect, 10, 10)

            painter.setPen(QColor("#2b2b2b"))

            # Add padding to the text
            text = "  " + text + "  "
            text_rect = painter.boundingRect(text_rect, Qt.AlignLeft | Qt.TextWordWrap, text)

            painter.drawText(text_rect, Qt.AlignLeft | Qt.TextWordWrap, text)

            painter.restore()

    def sizeHint(self, option, index):
        # get the text of the item
        text = index.data(Qt.DisplayRole)

        # get the font metrics of the text
        fontMetrics = option.fontMetrics

        # calculate a reasonable width for word-wrapping
        wrapWidth = option.rect.width() - 20  # 10 pixel padding on each side

        # calculate the bounding rect of the text if it is word-wrapped
        boundingRect = fontMetrics.boundingRect(0, 0, wrapWidth, 10000, Qt.AlignLeft | Qt.TextWordWrap, text)

        # calculate the number of lines in the text
        lines = text.split('\n')
        numLines = 0
        for line in lines:
            numLines += (fontMetrics.horizontalAdvance(line) // wrapWidth) + 1

        # calculate the height of the bounding rectangle based on the number of lines
        lineHeight = fontMetrics.height()
        boundingRect.setHeight(numLines * lineHeight + 10)  # add padding

        return boundingRect.size()

class JarvisWidget(QFrame):
    def __init__(self, parent=None):
        super(JarvisWidget, self).__init__(parent)
        print("Creating a JarvisWidget")
        self.chat_input = QLineEdit(self)
        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.process_query)
        self.chat_list_view = QListView(self)
        self.chat_list_view.setWordWrap(True)
        self.chat_list_model = QStandardItemModel(self.chat_list_view)
        self.chat_list_view.setModel(self.chat_list_model)
        self.chat_list_view.setItemDelegate(BubbleDelegate())


        self.web_search_checkbox = QCheckBox("Force web search", self)
        self.web_search_checkbox.setStyleSheet("background-color: #31363b; border-radius: 15px;")



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