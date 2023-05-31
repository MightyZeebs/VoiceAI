from voice_assistant.assistant import VoiceAssistant
from voice_assistant.utils import delete_audio_files
import sys
import threading
from PyQt5.QtWidgets import QApplication
from gui import MainWindow

def main():
    # Initialize voice assistant
    assistant = VoiceAssistant()
    # Create the GUI
    app = QApplication(sys.argv)
    window = MainWindow()  # Use MainWindow instead of VoiceAssistantApp
    window.show()
    window.voice_assistant = assistant  # Assign assistant to window.voice_assistant
    # Start the voice assistant's main thread
    voice_assistant_thread = threading.Thread(target=assistant.run, daemon=True)
    voice_assistant_thread.start()
    assistant.set_main_window(window)
    # Run the GUI event loop
    sys.exit(app.exec_())
if __name__ == "__main__":
    # Clean up audio files before starting
    delete_audio_files()

    # Start the program
    main()