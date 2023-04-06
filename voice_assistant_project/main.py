from voice_assistant import VoiceAssistant
from voice_assistant import delete_audio_files


def main():
    assistant = VoiceAssistant()

    assistant.activation_listener('alt+x', 'Gemini answer')

    assistant.run()

if __name__ == "__main__":
    delete_audio_files()
    main()