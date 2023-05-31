import os
import pygame
import sounddevice as sd
import soundfile as sf
import time
import threading
import numpy as np
import sys
import uuid
import requests
from elevenlabs import generate, save
from dotenv import load_dotenv
from google.cloud import texttospeech 
from .utils import audio_buffer
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesisOutputFormat, SpeechSynthesizer
from azure.cognitiveservices.speech.audio import AudioOutputConfig

load_dotenv()

play_speech_event = threading.Event()

def callback(indata, frames, time, status):
    # Define a callback function to handle audio data
    if status:
        print(status, file=sys.stderr)
    audio_buffer.put((indata.copy() * np.iinfo(np.int16).max).astype(np.int16))

def synthesize_speech(text):
    azure_api_key = os.getenv('AZURE_API_KEY')
    speech_config = SpeechConfig(subscription=azure_api_key, region="eastus")
    speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    speech_config.speech_synthesis_style_ids = ["assistant"]

    audio_file_name = f"audio_{uuid.uuid4().hex}.wav"
    audio_file_path = os.path.join("audio_files", audio_file_name)

    audio_output_config = AudioOutputConfig(filename=audio_file_path)
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)

    synthesizer.speak_text(text)

    print(f"saved audio to {audio_file_path}")
    return audio_file_path

class Player:
    def __init__(self):
        self.stream = sd.OutputStream(callback=self.audio_callback, samplerate=16000)
        self.data = None
        self.index = 0
        self.lock = threading.Lock()

    def audio_callback(self, outdata, frames, time, status):
        if status:
            print(status)
        with self.lock:
            if self.data is not None:
                remaining = len(self.data) - self.index
                if remaining >= frames:
                    to_write = self.data[self.index:self.index+frames]
                    self.index += frames
                else:
                    to_write = self.data[self.index:]
                    self.data = None
                outdata[:len(to_write)] = to_write.reshape((-1, 1))
                if len(to_write) < frames:
                    outdata[len(to_write):] = 0
            else:
                outdata[:] = 0

    def play(self, file):
        with self.lock:
            self.data, _ = sf.read(file, dtype='float32')
            self.index = 0
        if not self.stream.active:
            self.stream.start()

player = Player()

def play_speech_threaded(audio_file_path):
    play_thread = threading.Thread(target=player.play, args=(audio_file_path,), daemon=True)
    play_thread.start()


###############ELEVENLABS###############
# def sythesize_speech(text):
#     api_key = os.environ.get("ELEVENLABS_API_KEY")
#     if api_key is None:
#         print("API key not found. Please set the ELEVENLABS_API_KEY environment variable.")
#         return

#     voice = "Bella"
#     model = "eleven_monolingual_v1"

#     audio = generate(text, api_key=api_key, voice=voice, model=model)

#     audio_file_name = f"audio_{uuid.uuid4().hex}.mp3"
#     audio_file_path = os.path.join("audio_files", audio_file_name)
    
#     with open(audio_file_path, "wb") as audio_file:
#         audio_file.write(audio)
#         print(f"Saved audio to {audio_file_path}")

#     return audio_file_path

##############google text to speech#########################
#def sythesize_speech(text):
#     #text to speech using google
#     client = texttospeech.TextToSpeechClient()

#     input_text = texttospeech.SynthesisInput(ssml=text)
#     voice = texttospeech.VoiceSelectionParams(
#         language_code="en-US",
#         ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
#         name="en-US-Wavenet-C"
#     )
#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.LINEAR16,
#         speaking_rate=0.95, #default is 1
#         pitch=2.8, #default is 0

#     )
#     response = client.synthesize_speech(
#         input=input_text, voice=voice, audio_config=audio_config
#     )

#     audio_file_name = f"audio_{uuid.uuid4().hex}.wav"
#     audio_file_path = os.path.join("audio_files", audio_file_name)

#     with open(audio_file_path, "wb") as audio_file:
#         audio_file.write(response.audio_content)
#         print(f"saved audio to {audio_file_path}")

#     return audio_file_path

##############AZURE text to speech#########################
# def synthesize_speech(text):
#     azure_api_key = os.getenv('AZURE_API_KEY')
#     speech_config = SpeechConfig(subscription=azure_api_key, region="eastus")
#     speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
#     speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
#     speech_config.speech_synthesis_style_ids = ["assistant"]

#     audio_file_name = f"audio_{uuid.uuid4().hex}.wav"
#     audio_file_path = os.path.join("audio_files", audio_file_name)

#     audio_output_config = AudioOutputConfig(filename=audio_file_path)
#     synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)

#     synthesizer.speak_text(text)

#     print(f"saved audio to {audio_file_path}")
#     return audio_file_path