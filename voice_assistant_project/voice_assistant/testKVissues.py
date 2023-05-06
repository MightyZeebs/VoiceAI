from kivy.app import App
from kivy.lang import Builder
from kivymd.app import MDApp

class MyApp(MDApp):
    def build(self):
        return Builder.load_file('C:/Users/Zeebra/code/VoiceAI/voice_assistant_project/voice_assistant/voice_assistant_ui.kv')

if __name__ == '__main__':
    MyApp().run()



    
