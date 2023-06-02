from PyQt5.QtWidgets import QVBoxLayout, QLineEdit, QPushButton, QFrame, QCheckBox, QListView, QStyledItemDelegate
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPainter, QColor
from PyQt5.QtCore import pyqtSlot, Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QTextDocument


class QueryThread(QThread):
    response_signal = pyqtSignal(str)

    def __init__(self, voice_assistant, query):
        QThread.__init__(self)
        self.voice_assistant = voice_assistant
        self.query = query

    def run(self):
        assistant_response = self.voice_assistant.handle_transcript(self.query)
        self.response_signal.emit(assistant_response)

class BubbleDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(BubbleDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        if not index.isValid():
            return

        text = index.data(Qt.DisplayRole)
        if text:
            # Define text_rect before adjusting it based on wrapWidth
            text_rect = option.rect.adjusted(10, 5, -10, -5)
            
            # Calculate the size of the text and adjust the bubble accordingly
            fontMetrics = painter.fontMetrics()
            textWidth = fontMetrics.horizontalAdvance(text)
            wrapWidth = min(option.rect.width() - 20, textWidth + 20)  # 10 pixel padding on each side

            # Adjust text rect to accommodate the size of the text
            text_rect = text_rect.adjusted(0, 0, (wrapWidth - text_rect.width()), 0)

            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(Qt.NoPen)

            # Set the color according to the sender
            if text.startswith("User: "):
                painter.setBrush(QColor("#3daee9"))
                text = text[6:]
            else:
                painter.setBrush(QColor("#ee3d3d"))
                text = text[11:]

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

        # Create a QTextDocument because it supports 
        # "real" word-wrapping and can give us an accurate height.
        doc = QTextDocument()
        doc.setHtml(text)
        doc.setTextWidth(option.rect.width())

        # Round the width and height to the nearest integer
        width = round(doc.idealWidth())
        height = round(doc.size().height())

        padding = 10  # the amount of padding below each bubble

        return QSize(width, height + padding)

class JarvisWidget(QFrame):
    def __init__(self, parent=None):
        super(JarvisWidget, self).__init__(parent)
        print("Creating a JarvisWidget")
        self.deletable = True
        self.chat_input = QLineEdit(self)
        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.process_query)
        self.chat_list_view = QListView(self)
        self.chat_list_view.setWordWrap(True)
        self.chat_list_model = QStandardItemModel(self.chat_list_view)
        self.chat_list_view.setModel(self.chat_list_model)
        self.chat_list_view.setItemDelegate(BubbleDelegate())
        self.chat_input.returnPressed.connect(self.process_query)

        self.web_search_checkbox = QCheckBox("Force web search", self)
        self.web_search_checkbox.setStyleSheet("background-color: #31363b; border-radius: 15px;")

        # delete button for JarvisWidget
        self.jarvis_delete_button = QPushButton("X", self)
        self.jarvis_delete_button.clicked.connect(self.delete_jarvis)
        self.jarvis_delete_button.setFixedSize(25, 25)
        self.jarvis_delete_button.setStyleSheet("""
            background-color: #31363b;
            border-radius: 12px;
        """)


        self.chat_layout = QVBoxLayout()
        self.setLayout(self.chat_layout)

        # Include Jarvis delete button to layout
        self.chat_layout.addWidget(self.jarvis_delete_button, alignment=Qt.AlignTop | Qt.AlignRight)

        self.add_extra_content([self.chat_input, self.search_button, self.chat_list_view, self.web_search_checkbox])

        self.setStyleSheet("""
            JarvisWidget {
                background-color: #31363b;
                color: #eff0f1;
                border-radius: 15px;
                padding: 5px;
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

    # Added method to delete JarvisWidget
    def delete_jarvis(self):
        parent = self.parent()
        for i in reversed(range(parent.main_layout.count())): 
            widget = parent.main_layout.itemAt(i).widget()
            if widget is not None and isinstance(widget, JarvisWidget):
                widget.deleteLater()
                parent.has_widget = False  # Reset the has_widget flag
                parent.button.show()  # Show the button again
                parent.delete_button.show()  # Show the cell delete button again

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
            # Display the user's query immediately
            item = QStandardItem("User: " + query)
            self.chat_list_model.appendRow(item)
            self.chat_list_view.scrollToBottom()

            # Use a separate thread for processing the query
            self.query_thread = QueryThread(self.voice_assistant, query)
            self.query_thread.response_signal.connect(self.display_message)
            self.query_thread.start()

    def display_message(self, message):
        item = QStandardItem("Assistant: " + message)
        self.chat_list_model.appendRow(item)
        self.chat_list_view.scrollToBottom()