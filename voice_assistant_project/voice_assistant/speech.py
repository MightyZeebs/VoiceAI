import os
import tempfile
import pygame
import time
import threading
import numpy as np
import sys
import uuid
from google.cloud import texttospeech 
from .utils import audio_buffer
play_speech_event = threading.Event()

temp_files=[]
temp_files_lock = threading.Lock()

def callback(indata, frames, time, status):
    # Define a callback function to handle audio data
    if status:
        print(status, file=sys.stderr)
    audio_buffer.put((indata.copy() * np.iinfo(np.int16).max).astype(np.int16))

def sythesize_speech(text):
    #text to speech using google
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
        name="en-US-Standard-I"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )

    audio_file_name = f"audio_{uuid.uuid4().hex}.wav"
    audio_file_path = os.path.join("audio_files", audio_file_name)

    with open(audio_file_path, "wb") as audio_file:
        audio_file.write(response.audio_content)
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

        # Wait for the audio to finish playing and then delete the audio file
        while True:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT:
                    break
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
    finally:
        # Delete the audio file if an exception occurs
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)  

def play_speech_threaded(audio_file_path, stop_event=None):
    play_thread = threading.Thread(target=play_speech, args=(audio_file_path, stop_event), daemon=True)
    play_thread.start()