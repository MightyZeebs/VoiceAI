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
from voice_assistant.utils import audio_buffer
from .database import create_connection, create_table, insert_message
from .openai_integration import handle_question
from .speech import sythesize_speech, play_speech_threaded, callback
from threading import Lock

device_index = None
conversation_history = []

class VoiceAssistant:
    def __init__(self, deactivation_keyword="Jarvis stop"):
        self.root = None
        self.device_index = sd.default.device[0]
        self.stop_thread = False
        self.toggle_event = threading.Event()
        self.listening = False
        self.recording_thread = None
        self.deactivation_keyword = deactivation_keyword
        self.conn = create_connection("conversation_history.db")
        create_table(self.conn)
        self.conversation_history = []
        self.toggle_lock = Lock()
        self.main_thread_exited = threading.Event()
        self.stream = None
        self.activation_listener_thread = threading.Thread(target=self.activation_listener, args=('alt+x', '-'))
        self.activation_listener_thread.start()
        self.push_to_talk_mode = False
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US"
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config,
            interim_results=False
        )
    
    def audio_generator(self):
            global device_index

            while self.listening:
                if self.listening:
                    try:
                        data = audio_buffer.get(timeout=1)
                        yield speech.StreamingRecognizeRequest(audio_content=data.tobytes())
                    except queue.Empty:
                        pass
                else:
                    time.sleep(0.1)

    def run(self):
        print("starting 'run' thread")
        while not self.stop_thread:
            time.sleep(0.1)
            if self.listening and (self.recording_thread is None or not self.recording_thread.is_alive()):
                self.recording_thread = threading.Thread(target=self.record_and_transcribe, daemon=True)
                self.recording_thread.start()
                self.recording_thread.join()
        print("stopping 'run' thread")

    
    def toggle(self):
        with self.toggle_lock:
            self.listening = not self.listening
            print("listening flag flip")
            
            if self.listening:
                print("Voice assistant activated")
                self.toggle_event.clear()
            else:
                print("Voice assistant deactivated")
                self.toggle_event.set()



    def record_and_transcribe(self):    
        if self.listening:
            print("Recording started...")

            start_time = time.time()
            
            self.stream = sd.InputStream(device=self.device_index, samplerate=16000, channels=1, blocksize=2048, callback=callback, dtype=np.float32)
            self.stream.start()

            transcript_buffer = ""

            while self.listening and (not self.push_to_talk_mode or not self.toggle_event.is_set()):
                    elapsed_time = time.time() - start_time

                    if elapsed_time > 290:
                        if not self.is_speaking:
                            break

                    requests = self.audio_generator()
                    responses = self.client.streaming_recognize(self.streaming_config, requests=requests)
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
                                        break

                                    if self.push_to_talk_mode:
                                        transcript_buffer += " " + transcript
                                    else:
                                        self.handle_transcript(transcript)
                    except StopIteration:
                        pass
                    except Exception as e:
                        import traceback
                        print("An error occurred:", e)
                        traceback.print_exc()
                        break

            if self.push_to_talk_mode and transcript_buffer.strip():
                self.handle_transcript(transcript_buffer.strip())

            self.stream.stop()
        time.sleep(0.1)                  

    def activation_listener(self, hotkey, push_to_talk_hotkey):
        keyboard.add_hotkey(hotkey, self.toggle)
        keyboard.add_hotkey(push_to_talk_hotkey, self.start_push_to_talk, suppress=True, trigger_on_release=False)
        keyboard.add_hotkey(push_to_talk_hotkey, self.stop_push_to_talk, suppress=True, trigger_on_release=True)

    def start_push_to_talk(self):
        with self.toggle_lock:
            if not self.listening:
                self.listening = True
                self.push_to_talk_mode = True
                self.toggle_event.clear()
                print("Push to talk key pressed")
                
    def stop_push_to_talk(self):
        if self.listening and self.push_to_talk_mode:
            self.listening = False
            self.push_to_talk_mode = False
            self.toggle_event.set()
            print("Push to talk key released")
        
    def handle_transcript(self, transcript):
        print(f"[{time.strftime('%H:%M:%S')}] Sent to OpenAI API")
        Current_time = datetime.datetime.now()
        insert_message(self.conn, str(Current_time), "user", transcript)

        answer = handle_question(transcript, conversation_history, self.conn, Current_time, date_answer=None)
        audio_content = sythesize_speech(answer)
        print("assistant:", answer)
        self.is_speaking = True
        play_speech_threaded(audio_content)
        self.is_speaking = False

        Current_time = datetime.datetime.now()
        insert_message(self.conn, str(Current_time), "assistant", answer)
        conversation_history.append((Current_time, "assistant: " + answer))
        self.root.update_chat_box(transcript, answer)

    def set_deactivation_keyword(keyword):
        global deactivation_keyword
        deactivation_keyword = keyword
        print(f"Deactivation keyword set to '{keyword}'")
        
    def stop(self):
        self.stop_thread = True
        self.toggle_event.set()
        if self.recording_thread is not None:
            self.recording_thread.join(timeout=1)
        self.activation_listener_thread.join()
        self.conn.close()
        self.main_thread_exited.set()


