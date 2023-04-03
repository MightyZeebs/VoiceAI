import queue
import sounddevice as sd
import time
import numpy as np
import soundfile as sf
import datetime
import keyboard
import threading
import speech_recognition as sr
from google.cloud import speech
from .utils import audio_buffer
from .database import create_connection, create_table, insert_message
from .openai_integration import handle_question
from .speech import sythesize_speech, play_speech_threaded, callback


memory_history = []
device_index = None
conversation_history = []

class VoiceAssistant:
    def __init__(self, deactivation_keyword="Jarvis stop"):
        self.device_index = sd.default.device[0]
        self.stop_thread = False
        self.toggle_event = threading.Event()
        self.listening = False
        self.recording_thread = None
        self.deactivation_keyword = deactivation_keyword
        self.conn = create_connection("conversation_history.db")
        create_table(self.conn)

    def run(self):
        while not self.stop_thread:
            time.sleep(0.1)
    
    def toggle(self):
        self.listening = not self.listening
        print("listening flag flip")
        
        if self.listening:
            print("Voice assistant activated")
            self.toggle_event.clear()
            if self.recording_thread is None or not self.recording_thread.is_alive():
                self.recording_thread = threading.Thread(target=self.record_and_transcribe)
                self.recording_thread.start()

        else:
            print("Voice assistant deactivated")
            self.stop_recording()
            self.toggle_event.set()
            self.stop_recording()


    def record_and_transcribe(self):
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US"
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=False
        )

        def audio_generator():
            global device_index

            while not self.toggle_event.is_set():
                if self.listening:
                    try:
                        data = audio_buffer.get(timeout=1)
                        yield speech.StreamingRecognizeRequest(audio_content=data.tobytes())
                    except queue.Empty:
                        pass
                else:
                    time.sleep(0.1)

        if self.listening:
            print("Recording started...")

            with sd.InputStream(device=device_index, samplerate=16000, channels=1, blocksize=2048, callback=callback, dtype=np.float32) as stream:
                while self.listening:
                    transcript = ""
                    requests = audio_generator()
                    responses = client.streaming_recognize(streaming_config, requests=requests)
                    response_iterator = iter(responses)

                    try:                      
                        for response in response_iterator:
                            if not response.results:
                                print("No transcription results found.")
                            else:
                                result = response.results[-1]
                                if result.is_final:
                                    transcript = result.alternatives[0].transcript
                                    print("user:", transcript)

                                    if self.deactivation_keyword.lower() in transcript.lower():
                                        self.toggle()
                                    if self.listening:

                                        Current_time = datetime.datetime.now()
                                        insert_message(self.conn, str(Current_time), "user", transcript)

                                        answer = handle_question(transcript, conversation_history, memory_history, self.conn)
                                        audio_content = sythesize_speech(answer)
                                        print("assistant:", answer)
                                        play_speech_threaded(audio_content)

                                        Current_time = datetime.datetime.now()
                                        insert_message(self.conn, str(Current_time), "assistant", answer)
                                        conversation_history.append((Current_time, "assistant: " + answer))
                    except StopIteration:
                        pass
                    except Exception as e:
                        import traceback
                        print("An error occurred:", e)
                        traceback.print_exc()
                        break

    def stop_recording(self):
        if self.recording_thread is not None and self.recording_thread is not threading.current_thread():
            self.toggle_event.set()
            self.recording_thread.join()
            self.recording_thread = None

    def activation_listener(self, hotkey, keyword):
        keyboard.add_hotkey(hotkey, self.toggle)

        r = sr.Recognizer()
        r.energy_threshold = 1500
        microphone = sr.Microphone()

        while not self.stop_thread:
            if not self.listening:
                activation_keyword = keyword.lower()
                print("Listening for activation...")
                try:
                    with microphone as source:
                        r.adjust_for_ambient_noise(source)
                        audio = r.listen(source)
                        if self.listening:
                            continue
                        print("Processing audio...")

                    recognized_text = r.recognize_sphinx(audio)
                    print("Recognized text:", recognized_text)

                    if activation_keyword in recognized_text.lower():
                        self.toggle()

                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print("Error occurred during sphinx recognition:", e)

            time.sleep(0.1)
                
                