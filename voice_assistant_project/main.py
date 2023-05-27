from voice_assistant.assistant import VoiceAssistant
from voice_assistant.utils import delete_audio_files
import sys
import threading
from PyQt5.QtWidgets import QApplication
from gui import VoiceAssistantApp
def main():
    # Initialize voice assistant
    assistant = VoiceAssistant()

    # Create the GUI
    app = QApplication(sys.argv)
    voice_assistant_app = VoiceAssistantApp(assistant)
    voice_assistant_app.show()

    # Run the GUI event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Clean up audio files before starting
    delete_audio_files()

    # Start the program
    main()