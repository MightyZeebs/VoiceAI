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

# Save the recorded audio to a file
def save_audio_to_file(audio_data, audio_data_filename):
    with sf.SoundFile(audio_data_filename, mode='x', samplerate=16000, channels=1, subtype='PCM_16') as file:
        file.write(audio_data)

# Record and transcribe the audio
def record_and_transcribe(duration):
    recorded_audio = np.empty((0, 1), dtype=np.int16)

    with sd.InputStream(samplerate=16000, channels=1, dtype=np.int16, blocksize=8000, callback=callback):
        print("Recording started...")
        time.sleep(duration)
        print("Recording finished...")

    while not audio_buffer.empty():
        recorded_audio = np.append(recorded_audio, audio_buffer.get(), axis=0)

    # Save the recorded audio to a file
    save_audio_to_file(recorded_audio, "recorded_audio.wav")

    # Set up the client
    client = speech.SpeechClient()

    # Configure the speech recognition settings
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    # Read the recorded audio file
    with io.open("recorded_audio.wav", "rb") as audio_file:
        content = audio_file.read()

    # Prepare the audio to send to the API
    audio = speech.RecognitionAudio(content=content)

    # Perform the transcription using the long_running_recognize method
    operation = client.long_running_recognize(config=config, audio=audio)

    # Wait for the operation to complete
    print("Waiting for the operation to complete...")
    response = operation.result(timeout=90)

    # Print the transcribed text
    if not response.results:
        print("No transcription results found.")
    else:
        for result in response.results:
            print(result.alternatives[0].transcript)

record_and_transcribe(duration=20)  # Record for 20 seconds