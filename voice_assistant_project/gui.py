from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
import datetime
import os
import sys
import threading
from voice_assistant.speech import synthesize_speech, play_speech_threaded
from voice_assistant.openai_integration import handle_question
from voice_assistant import assistant
from kivy.core.clipboard import Clipboard
from kivy.uix.button import Button
from kivy.config import Config
from pynput.keyboard import Controller
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.factory import Factory
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.lang import Builder


Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

class WrappedButton(Button):
    def __init__(self, **kwargs):
        # Call the parent constructor with the same arguments
        super().__init__(**kwargs)
        # Make the button look like a label by removing its background
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        # Align the text to the left (you might need to adjust this depending on your design)
        self.halign = 'left'

    def on_release(self):
        # When the button is clicked, copy its text to the clipboard
        Clipboard.copy(self.text)

class VoiceAssistantUI(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        self.keyboard = Controller()

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

    def simulate_key_press(self, key):
        self.keyboard.press(key)
        self.keyboard.release(key)
  
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

            # Change this to create an instance of WrappedButton instead of WrappedLabel
            assistant_message_item = WrappedButton(text=f"Assistant: {assistant_message}")

            if user_message:
                # Same change here
                user_message_item = WrappedButton(text=f"User: {user_message}")
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


