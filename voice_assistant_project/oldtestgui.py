import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QTextEdit,
    QLabel,
    QScrollArea,
)
from voice_assistant.speech import synthesize_speech, play_speech_threaded
from voice_assistant.openai_integration import handle_question
from pynput.keyboard import Controller
import datetime
import threading


class ChatBubble(QPushButton):
    def __init__(self, text, bubble_color, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setStyleSheet("background-color: rgba{0, 0, 0, 0};")
        self.setAlignment(Qt.AlignLeft)
        self.bubble_color = bubble_color

    def mouseReleaseEvent(self, event):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text())


class VoiceAssistantUI(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app.assistant
        self.keyboard = Controller()

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.user_input = QTextEdit(self)
        self.user_input.setMaximumHeight(40)
        self.layout.addWidget(self.user_input)

        self.force_web_search_button = QPushButton("Force Web Search", self)
        self.force_web_search_button.setCheckable(True)
        self.force_web_search_button.clicked.connect(self.force_web_search)
        self.layout.addWidget(self.force_web_search_button)

        self.output_container = QWidget(self)
        self.output_layout = QVBoxLayout(self.output_container)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.output_container)
        self.layout.addWidget(self.scroll_area)

    def force_web_search(self):
        self.app.assistant.force_web_search = not self.app.assistant.force_web_search
        state = "on" if self.app.assistant.force_web_search else "off"
        self.force_web_search_button.setText(f"Force Web Search ({state})")
        message = f"Forced web search is now {state}"
        audio_file_path = synthesize_speech(message)
        play_speech_threaded(audio_file_path)

    def process_query(self, query):
        self.user_input.clear()
        self.user_input.setFocus(Qt.OtherFocusReason)
        if query:
            self.update_user_message_in_chat_box(query)
            threading.Thread(target=self.process_query_thread, args=(query,)).start()

    def process_query_thread(self, query):
        if query:
            current_time = datetime.datetime.now()
            if query.lower() == "reset chat":
                self.reset_chat()
                assistant_message = "Chat has been successfully reset."
                audio_file_path = synthesize_speech(assistant_message)
                play_speech_threaded(audio_file_path)
                self.update_chat_box("", assistant_message)
            else:
                print("User:", query)
                response = handle_question(query, self.app.conn, current_time, self)
                audio_file_path = synthesize_speech(response)
                play_speech_threaded(audio_file_path)
                self.update_chat_box(query, response)

    def simulate_key_press(self, key):
        self.keyboard.press(key)
        self.keyboard.release(key)

    def clear_chat_box(self):
        for i in reversed(range(self.output_layout.count())):
            self.output_layout.itemAt(i).widget().deleteLater()

    def reset_chat(self):
        self.clear_chat_box()
        current_time = datetime.datetime.now()
        handle_question("reset chat", self.app.assistant.conn, current_time, self)
        assistant_message = "Chat has been successfully reset."
        audio_file_path = synthesize_speech(assistant_message)
        play_speech_threaded(audio_file_path)
        self.update_chat_box("", assistant_message)

    def update_user_message_in_chat_box(self, user_message):
        if self.layout.count() > 3:
            self.layout.itemAt(2).widget().deleteLater()
        user_message_item = ChatBubble(f"User: {user_message}", [1, 0, 0, 0.5], self.output_container)
        self.output_layout.addWidget(user_message_item)

    def update_chat_box(self, user_message, assistant_message):
        if self.layout.count() > 3:
            self.layout.itemAt(2).widget().deleteLater()
        assistant_message_item = ChatBubble(f"Assistant: {assistant_message}", [0, 0, 1, 0.5], self.output_container)
        self.output_layout.addWidget(assistant_message_item)


class VoiceAssistantApp(QMainWindow):
    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 400, 600)

        self.voice_assistant_ui = VoiceAssistantUI(self)
        self.setCentralWidget(self.voice_assistant_ui)

    def process_query(self, query):
        self.voice_assistant_ui.process_query(query)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_voice_assistant = VoiceAssistantUI(app)
    voice_assistant_app = VoiceAssistantApp(my_voice_assistant)
    voice_assistant_app.show()
    sys.exit(app.exec_())