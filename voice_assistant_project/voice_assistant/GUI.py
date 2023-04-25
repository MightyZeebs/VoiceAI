import datetime
import tkinter as tk
from tkinter import ttk
from voice_assistant import sythesize_speech, play_speech_threaded
from voice_assistant.openai_integration import handle_question

def create_GUI(assistant):
    def process_query():
        query = entry.get()
        if query:
            current_time = datetime.datetime.now()
            response = handle_question(query, assistant.conversation_history, assistant.memory_history, assistant.conn, current_time, date_answer=None)
            audio_file_path = sythesize_speech(response)
            play_speech_threaded(audio_file_path)
            response_label.config(text=response)

    def toggle_voice_activation():
        assistant.toggle()

    root = tk.Tk()
    root.title("Voice Assistant GUI")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    entry = ttk.Entry(frame, width=50)
    entry.grid(row=1, column=0, sticky=(tk.W, tk.E))

    search_button = ttk.Button(frame, text="Search", command=process_query)
    search_button.grid(row=2, column=0, sticky=tk.W)

    response_label = ttk.Label(frame, text="")
    response_label.grid(row=3, column=0, sticky=tk.W)

    toggle_button = ttk.Button(frame, text="Toggle Voice Activation", command=toggle_voice_activation)
    toggle_button.grid(row=4, column=0, sticky=tk.W)

    return root
