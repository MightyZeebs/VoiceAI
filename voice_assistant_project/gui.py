from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
import datetime
import os
from voice_assistant.speech import synthesize_speech, play_speech_threaded
from voice_assistant.openai_integration import handle_question
from voice_assistant import assistant
import sys
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.list import OneLineListItem
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.metrics import dp

class VoiceAssistantUI(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    def process_query(self, query):
        if query:
            print("User: ", query)
            current_time = datetime.datetime.now()
            response = handle_question(query, self.app.assistant.conn, current_time, self)
            audio_file_path = synthesize_speech(response)
            play_speech_threaded(audio_file_path)
            self.update_chat_box(query, response)
            self.ids.user_input.text = ""
  
    def clear_chat_box(self):
        self.ids.output_container.clear_widgets()

    def update_chat_box(self, user_message, assistant_message):
        def update(dt):
            if self.ids.welcome_message.parent is not None:
                self.ids.output_container.remove_widget(self.ids.welcome_message)

            user_message_item = Factory.WrappedLabel(text=f"User: {user_message}")
            assistant_message_item = Factory.WrappedLabel(text=f"Assistant: {assistant_message}")

            self.ids.output_container.add_widget(user_message_item)
            self.ids.output_container.add_widget(assistant_message_item)

        Clock.schedule_once(update, 0)


class VoiceAssistantApp(MDApp):
    def __init__(self, assistant, **kwargs):
        self.assistant = assistant
        super().__init__(**kwargs)

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        #print(f"Loading .kv code")
        
        # Load the kv file first
        kv_file_path = os.path.join(os.path.dirname(__file__), 'ui.kv')
        Builder.load_file(kv_file_path)

        # Then create an instance of VoiceAssistantUI
        voice_assistant_ui = VoiceAssistantUI(self)
        voice_assistant_ui.assistant = self.assistant
        #print("KV code loaded successfully")
        return voice_assistant_ui

    def process_query(self, query):
        self.root.process_query(query)

Factory.register('VoiceAssistantUI', cls=VoiceAssistantUI)


