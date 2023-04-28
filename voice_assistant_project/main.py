from voice_assistant import VoiceAssistant, delete_audio_files
from voice_assistant.GUI import create_GUI
import threading

def main():
    assistant = VoiceAssistant()

    assistant_run_thread = threading.Thread(target=assistant.run)
    assistant_run_thread.start()

    root = create_GUI(assistant)
    root.mainloop()
    assistant.stop()

if __name__ == "__main__":
    delete_audio_files()
    main()

