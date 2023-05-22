from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
import datetime
import os
import sys
import threading
from voice_assistant.speech import synthesize_speech, play_speech_threaded
from voice_assistant.openai_integration import handle_question
from voice_assistant import assistant
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.list import OneLineListItem
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.config import Config

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

class VoiceAssistantUI(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    def process_query(self, query):
        self.ids.user_input.text = ""
        Clock.schedule_once(self.set_focus, 0)
        if query:
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
                print("User: ", query)
                response = handle_question(query, self.app.assistant.conn, current_time, self)
                audio_file_path = synthesize_speech(response)
                play_speech_threaded(audio_file_path)
                self.update_chat_box(query, response)


    def set_focus(self, dt):
        self.ids.user_input.focus = True
  
    def clear_chat_box(self):
        def clear(dt):
            self.ids.output_container.clear_widgets()
        Clock.schedule_once(clear)

    def reset_chat(self):
        self.clear_chat_box()
        current_time = datetime.datetime.now()
        handle_question("reset chat", self.app.assistant.conn, current_time, self)
        assistant_message = "Chat has been successfully reset."
        audio_file_path = synthesize_speech(assistant_message)
        play_speech_threaded(audio_file_path)
        self.update_chat_box("", assistant_message)


    def update_chat_box(self, user_message, assistant_message):
        def update(dt):
            if 'welcome_message' in self.ids and self.ids.welcome_message.parent is not None:
                self.ids.output_container.remove_widget(self.ids.welcome_message)

            assistant_message_item = Factory.WrappedLabel(text=f"Assistant: {assistant_message}")
            
            if user_message:
                user_message_item = Factory.WrappedLabel(text=f"User: {user_message}")
                self.ids.output_container.add_widget(user_message_item)
            
            self.ids.output_container.add_widget(assistant_message_item)
            Clock.schedule_once(lambda dt: self.ids.scroll_view.scroll_to(assistant_message_item), 0.1)
            self.ids.scroll_view.scroll_to(assistant_message_item)

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
        self.voice_assistant_ui = VoiceAssistantUI(self)
        #print("KV code loaded successfully")
        return voice_assistant_ui

    def process_query(self, query):
        self.root.process_query(query)

Factory.register('VoiceAssistantUI', cls=VoiceAssistantUI)


