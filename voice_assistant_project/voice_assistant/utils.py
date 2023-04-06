import queue
import glob
import os

def delete_audio_files():
    audio_files = glob.glob("audio_files/*.wav")
    for audio_file in audio_files:
        try:
            os.remove(audio_file)
            print(f"Deleted: {audio_file}")
        except Exception as e:
            print(f"failed to delete {audio_file}: e")

audio_buffer = queue.Queue() # Create a thread-safe buffer to store audio data