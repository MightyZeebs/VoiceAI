import os
import librosa
import numpy as np
import scipy.signal
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from dotenv import load_dotenv

load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_API_KEY")

from azure.cognitiveservices.speech import (
    SpeechConfig,
    SpeechSynthesizer,
    AudioConfig,
    SpeechSynthesisOutputFormat,
    ResultReason,
)

import soundfile as sf

def process_audio(audio_file_path, sr):
    print("Processing audio...")

    # Load the audio file
    audio, sr = librosa.load(audio_file_path, sr=None, mono=True)

    # Apply equalization
    print("Applying equalization...")
    b, a = scipy.signal.butter(1, [300/(sr/2), 3400/(sr/2)], btype='band')
    audio = scipy.signal.lfilter(b, a, audio)

    # Apply pitch modulation
    print("Applying pitch modulation...")
    pitch_modulation_range = 2  # The maximum pitch shift in semitones
    pitch_modulation_rate = 0.5  # The rate of pitch modulation in Hz
    pitch_modulation = pitch_modulation_range * np.sin(2 * np.pi * pitch_modulation_rate * np.arange(len(audio)) / sr)
    pitch_modulated_audio = librosa.effects.pitch_shift(audio, sr, n_steps=pitch_modulation)

    # Save the pitch-modulated audio as a temporary file
    temp_file_path = "temp_pitch_modulated.wav"
    sf.write(temp_file_path, pitch_modulated_audio, sr)

    # Load the pitch-modulated audio with pydub
    modulated_audio = AudioSegment.from_wav(temp_file_path)

    # Apply compression
    print("Applying compression...")
    compressed_audio = compress_dynamic_range(modulated_audio, threshold=-20.0, ratio=2.0, attack=5, release=200)

    # Normalize the audio
    print("Normalizing audio...")
    normalized_audio = normalize(compressed_audio)

    # Save the processed audio
    processed_audio_file_path = f"{os.path.splitext(audio_file_path)[0]}_processed.wav"
    normalized_audio.export(processed_audio_file_path, format="wav")
    return processed_audio_file_path




def synthesize_speech(text, sr):
    speech_config = SpeechConfig(subscription=AZURE_API_KEY, region="eastus")
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    speech_config.speech_synthesis_language = "en-US"
    speech_config.set_speech_synthesis_output_format(SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)

    audio_config = AudioConfig(filename="test_output.wav")
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    response_text = f"{text} <prosody rate='100%' pitch='+20%'>Ha</prosody><prosody rate='90%' pitch='+10%'>ha</prosody><prosody rate='80%'>ha</prosody> I hope you're having a good day! <prosody rate='50%' pitch='-30%'>Ahh</prosody><prosody rate='50%' pitch='-40%'>hh</prosody>"
    response_ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'><voice name='en-US-JennyNeural'>{response_text}</voice></speak>"

    result = synthesizer.speak_ssml_async(response_ssml).get()

    if result.reason == ResultReason.SynthesizingAudioCompleted:
        print("Audio synthesized and saved to test_output.wav")
        
        # Process the audio and save the result
        processed_audio_file_path = process_audio("test_output.wav", sr)
        print(f"Processed audio saved to {processed_audio_file_path}")
    else:
        cancellation_details = result.cancellation_details
        print(f"Error: {cancellation_details.error_details}")

text = "Hello! This is a test using Azure Text-to-Speech with the Jenny voice in Assistant style."
sr = 16000
synthesize_speech(text, sr)






