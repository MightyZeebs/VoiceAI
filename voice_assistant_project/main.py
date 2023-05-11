from voice_assistant.assistant import VoiceAssistant
from voice_assistant.utils import delete_audio_files, load_model, load_data, preprocess_text, predict_question
from gui import VoiceAssistantApp
import threading

def main():
    assistant = VoiceAssistant()

    app = VoiceAssistantApp(assistant=assistant)
    assistant.app = app

    assistant_run_thread = threading.Thread(target=assistant.run)
    assistant_run_thread.start()

    app.run()
    assistant.stop()



if __name__ == "__main__":
    delete_audio_files()
    main()