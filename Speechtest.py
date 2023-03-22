import io
import queue
import sounddevice as sd
import sys
import time
import numpy as np
import soundfile as sf

# Import the Google Cloud client library
from google.cloud import speech

# Create a thread-safe buffer to store audio data
audio_buffer = queue.Queue()

# Define a callback function to handle audio data
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_buffer.put(indata.copy())
    print("sample rate:", sd.query_devices(sd.default.device)['default_samplerate'])

# Save the recorded audio to a file
def save_audio_to_file(audio_data, audio_data_filename):
    with sf.SoundFile(audio_data_filename, mode='x', samplerate=16000, channels=1, subtype='PCM_16') as file:
        file.write(audio_data)

# Record and transcribe the audio
def record_and_transcribe(duration):
    # Set up the client
    client = speech.SpeechClient()

    # Configure the speech recognition settings
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=16000,
        language_code="en-US"
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    #get the microphone index
    def get_microphone_index():
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['name'] == "Microphone (Voicemod Virtual Audio Device (WDM))":
                return i
        return None
        
    device_index = get_microphone_index()
    if device_index is None:
        print("Default microphone not found.")
    else:
        print(f"Using default microphone (index {device_index}).")

    # Create a generator that yields audio chunks
    def audio_generator():
        with sd.InputStream(device=device_index, samplerate=48000, channels=1, blocksize=1024, callback=callback):
            print("Recording started...")
            while True:
                try:
                    data = audio_buffer.get(timeout=5)
                    print("Data length:", len(data))
                    yield speech.RecognitionAudio(content=data.tobytes())
                except queue.Empty:
                    break   
            
            print("Recording finished...")

    requests = audio_generator()
    responses = client.streaming_recognize(streaming_config, requests=requests)

    # Process the responses
    for response in responses:
        print("Response:", response)
        if not response.results:
            print("No transcription results found.")
        else:
            for result in response.results:
                print(result.alternatives[0].transcript)

record_and_transcribe(duration=10)  # Record for 10 seconds
