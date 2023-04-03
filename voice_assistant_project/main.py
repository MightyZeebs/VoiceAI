from voice_assistant import VoiceAssistant

def main():
    assistant = VoiceAssistant()

    assistant.activation_listener('alt+x', 'Jarvis answer')

    assistant.run()

if __name__ == "__main__":
    main()