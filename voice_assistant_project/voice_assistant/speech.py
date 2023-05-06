import os
import pygame
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


def play_speech(audio_file_path, stop_event=None):
    # Set environment variable to hide the pygame support prompt
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    
    # Initialize pygame
    pygame.init()
    pygame.mixer.init()

    try:
        # Load the audio file
       with open(audio_file_path,"rb") as f:
        pygame.mixer.music.load(f)
        pygame.mixer.music.play()

        # Event to detect when audio is finished
        pygame.mixer.music.set_endevent(pygame.USEREVENT)

        audio_finished = False
        while not audio_finished:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT:
                    audio_finished = True
            if stop_event and stop_event.is_set():
                    pygame.mixer.music.stop()
            pygame.time.Clock().tick(10)


    except pygame.error as e:
        print(f"Error occurred while playing speech: {e}")
        while True:
            try:
                # Wait for a short delay before retrying
                time.sleep(0.5)

                # Try loading the audio file again
                with open(audio_file_path, "rb") as f:
                    pygame.mixer.music.load(f)
                    pygame.mixer.music.play()

                break
            except pygame.error:
                # If the error occurs again, retry after a longer delay
                time.sleep(1)

def play_speech_threaded(audio_file_path, stop_event=None):
    play_thread = threading.Thread(target=play_speech, args=(audio_file_path, stop_event), daemon=True)
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
