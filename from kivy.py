from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.button import MDIconButton
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.behaviors import ButtonBehavior

class RoundedButton(ButtonBehavior, MDFloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [1, 0, 0, 1] # set the color you want here
        self.radius = [25,]  # Set the radius for the rounded corners
        self.elevation = 8
        icon = MDIconButton(icon="android", pos_hint={'center_x': .5, 'center_y': .5})
        self.add_widget(icon)

class TestApp(MDApp):
    def build(self):
        return RoundedButton()

TestApp().run()
