import datetime
import pystray
import tkinter as tk
from tkinter import ttk
from voice_assistant import sythesize_speech, play_speech_threaded
from voice_assistant.openai_integration import handle_question
from PIL import Image
import sys
import threading

def create_GUI(assistant):
    def process_query():
        query = entry.get()
        if query:
            current_time = datetime.datetime.now()
            response = handle_question(query, assistant.conversation_history, assistant.conn, current_time, date_answer=None)
            audio_file_path = sythesize_speech(response)
            play_speech_threaded(audio_file_path)
            response_label.config(text=response)
            chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, "User: " + query + "\n")
            chat_box.insert(tk.END, "Assistant: " + response + "\n")
            chat_box.config(state=tk.DISABLED)

            
    def shutdown():
        assistant.stop()
        root.destroy()
        main_thread = threading.current_thread()
        for t in threading.enumerate():
            if t is not main_thread:
                t.join(timeout=1)
        sys.modules['voice_assistant.speech'].play_speech_event.set()
        assistant.main_thread_exited.set()
        sys.exit()

    def on_closing():
        minimize_to_tray(root)

    def on_restore(icon, item):
        icon.stop()
        root.deiconify()
        root.protocol("WM_DELTE_WINDOW", on_closing)
        root.update()
    
    def minimize_to_tray(root):
        root.iconify()
        root.overrideredirect(True)        
        tray_icon_image = Image.open("C:\\Users\\Zeebra\\code\\VoiceAI\\Jarvis.jfif")
        tray_icon = pystray.Icon("name", tray_icon_image, "My System Tray Icon", menu=pystray.Menu(pystray.MenuItem('Open', on_restore)))
        tray_icon.run()

    def toggle_voice_activation():
        assistant.toggle()
    
    # def set_deactivation_keyword(keyword):
    #     global deactivation_keyword
    #     deactivation_keyword = keyword
    #     print(f"Deactivation keyword set to '{keyword}'")

    def reset_chat():
        chat_box.config(state=tk.NORMAL)
        chat_box.delete('1.0', tk.END)
        chat_box.config(state=tk.DISABLED)
        handle_question("Let's start fresh and forget everything we talked about before", assistant.conversation_history, assistant.conn, datetime.datetime.now(), date_answer=None)
        return

    root = tk.Tk()
    root.title("Voice Assistant GUI")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    entry = ttk.Entry(frame, width=50)
    entry.grid(row=1, column=0, sticky=(tk.W, tk.E))

    search_button = ttk.Button(frame, text="Search", command=process_query)
    search_button.grid(row=2, column=0, sticky=tk.W)

    response_text = tk.StringVar()
    response_label = ttk.Label(frame, textvariable=response_text)
    response_label.grid(row=3, column=0, sticky=tk.W)

    # Chat box
    chat_box = tk.Text(frame, height=10, width=50)
    chat_box.config(state=tk.DISABLED)
    chat_box.grid(row=6, column=0, sticky=tk.W)

    # Set deactivation keyword button
    # set_deactivation_keyword_button = ttk.Button(frame, text="Set Deactivation Keyword", command=set_deactivation_keyword)
    # set_deactivation_keyword_button.grid(row=6, column=0, sticky=tk.W)

    # Reset chat button
    reset_chat_button = ttk.Button(frame, text="Reset Chat", command=reset_chat)
    reset_chat_button.grid(row=5, column=0, sticky=tk.W)

    #shutdown button 
    shutdown_button = tk.Button(root, text="Shutdown", command=shutdown)
    shutdown_button.grid(row=7, column=0, sticky='se')


    toggle_button = ttk.Button(frame, text="Toggle Voice Activation", command=toggle_voice_activation)
    toggle_button.grid(row=4, column=0, sticky=tk.W)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    return root