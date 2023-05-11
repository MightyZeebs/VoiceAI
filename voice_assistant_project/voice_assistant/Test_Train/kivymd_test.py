from kivymd.app import MDApp
from kivy.lang import Builder

class KivyMDTestApp(MDApp):
    def build(self):
        return Builder.load_file('kivymd_test.kv')

if __name__ == '__main__':
    KivyMDTestApp().run()
