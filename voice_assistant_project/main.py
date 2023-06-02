from voice_assistant.assistant import VoiceAssistant
from voice_assistant.utils import delete_audio_files
import sys
import threading
from PyQt5.QtWidgets import QApplication
from gui import MainWindow
from jarvis import JarvisWidget

def main():
    # Create the GUI
    app = QApplication(sys.argv)

    # Create JarvisWidget instance
    jarvis_widget = JarvisWidget()

    # Initialize voice assistant with JarvisWidget instance
    assistant = VoiceAssistant(jarvis_widget=jarvis_widget)

    window = MainWindow()
    window.show()
    window.set_voice_assistant(assistant)  # Use set_voice_assistant method to assign assistant to window

    # Start the voice assistant's main thread
    voice_assistant_thread = threading.Thread(target=assistant.run, daemon=True)
    voice_assistant_thread.start()

    # Set the JarvisWidget for VoiceAssistant
    assistant.set_main_window(window)

    # Run the GUI event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Clean up audio files before starting
    delete_audio_files()

    # Start the program
    main()
