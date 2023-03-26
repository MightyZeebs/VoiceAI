import io
import os
import queue
import sounddevice as sd
import sys
import time
import numpy as np
import soundfile as sf
import openai
import sqlite3
import datetime
import tempfile
import pygame
import keyboard
import threading
from google.cloud import speech # Import the Google Cloud client library
from google.cloud import texttospeech
audio_buffer = queue.Queue()
    # Create a thread-safe buffer to store audio data

memory_history = []

def create_connection():
    #create a connection to the SQLite database
    conn = None
    try:
        conn = sqlite3.connect('conversation_history.db', check_same_thread=False)
        print(f'Successfully connected to SQLite version {sqlite3.version}')
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    #create a table to store conversation history
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversation_history
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    text TEXT NOT NULL);''')
        conn.commit()
        print('successfully created conversation history table.')
    except sqlite3.Error as e:
        print(e)

def initialize_database():
    conn = create_connection()
    create_table(conn)
    return conn

def insert_message(conn, timestamp, speaker, text):
    #insert a message into the conversation history table
    try:
        c = conn.cursor()
        c.execute("INSERT INTO conversation_history (timestamp, speaker, text) VALUES (?, ?, ?)", (timestamp, speaker, text))
        conn.commit()
    except sqlite3.Error as e:
        print(e)

    
def retrieve_database_history(conn, minutes=5):
    #retrieve the conversation history from the database
    current_time = datetime.datetime.now()
    time_threshold = current_time - datetime.timedelta(minutes=minutes)
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM conversation_history WHERE timestamp >= ?", (time_threshold,))
        rows = c.fetchall()
        return [(datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f"
), row[2], row[3]) for row in rows] if rows else [] #return an empty list if rows are empty
    except sqlite3.Error as e:
        print(e)
        return []

def retrieve_memory_history(conversation_history, minutes=5):
    current_time = datetime.datetime.now()
    time_threshold = current_time - datetime.timedelta(minutes=minutes)
    memory_history = [item for item in conversation_history if item[0] >= time_threshold]
    return memory_history

def callback(indata, frames, time, status):
    # Define a callback function to handle audio data
    if status:
        print(status, file=sys.stderr)
    audio_buffer.put((indata.copy() * np.iinfo(np.int16).max).astype(np.int16))

conversation_history = []

def handle_question(question, conversation_history, conn):
    #Define how to the AI handles questions and understands previous context
    current_time = datetime.datetime.now()
    insert_message(conn, current_time, "user", question)
    
    if memory_history:
        conversation_history = retrieve_memory_history(memory_history, 5)
    else:
        conversation_history = retrieve_database_history(conn, 5)
            #if there is no conversation in memory it will use it otherwise pulls from the database

    recall_phrase = ["remember when", "recall", "search for"]
    first_words = " ".join(question.lower().split()[:3])
    if any(first_words.startswith(phrase) for phrase in recall_phrase):
        filtered_history = conversation_history #use entire conversation history as context
    else:
        #use only the last 5 minutes of conversation as context
        filtered_history = [
            entry for entry in conversation_history
            if (current_time - entry[0]) <= datetime.timedelta(minutes=5)
        ]

    history_str = "\n".join(f"{entry[1]}: {entry[2]}" for entry in filtered_history)

    prompt = f"{history_str}\nUser: {question}\nAssistnat:"

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.5,
    )

    answer = response.choices[0].text.strip()
    conversation_history.append((current_time, "Assistant: " + answer))
    return answer

def sythesize_speech(text):
    #text to speech using google
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
        name="en-GB-Standard-B"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        temp_file.write(response.audio_content)
        temp_file_path = temp_file.name
            #save the audio content to a temp file

    return temp_file_path

def play_speech(audio_file_path):
    # Set environment variable to hide the pygame support prompt
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    
    # Initialize pygame
    pygame.init()
    pygame.mixer.init()

    # Load the audio file
    pygame.mixer.music.load(audio_file_path)

    # Event to detect when audio is finished
    pygame.mixer.music.set_endevent(pygame.USEREVENT)

    # Play the audio file
    pygame.mixer.music.play()

    # Wait for the audio to finish playing and then delete the audio file
    while True:
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                pygame.mixer.music.stop()
                while True:
                    try:
                        os.remove(audio_file_path)
                        break
                    except PermissionError:
                        time.sleep(0.1)
                return
        pygame.time.Clock().tick(10)

stream = None
device_index = None


def record_and_transcribe(conn):
    global listening
    global stream
    global device_index

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
        global listening
        global device_index

        while True:
            if listening:
                try:
                    data = audio_buffer.get(timeout=1)
                    audio_request = speech.RecognitionAudio(content=data.tobytes())
                    yield speech.StreamingRecognizeRequest(audio_content=audio_request.content)
                except queue.Empty:
                    pass
            else:
                break

    if listening:
        print("Recording started...")

        with sd.InputStream(device=device_index, samplerate=16000, channels=1, blocksize=1024, callback=callback, dtype=np.float32) as stream:
            while listening:
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

                                Current_time = datetime.datetime.now()
                                insert_message(conn, str(Current_time), "user", transcript)

                                answer = handle_question(transcript, conversation_history, conn)
                                audio_content = sythesize_speech(answer)
                                print("assistant:", answer)
                                play_speech(audio_content)

                                Current_time = datetime.datetime.now()
                                insert_message(conn, str(Current_time), "assistant", answer)
                                insert_message(conn, str(Current_time), "user", transcript)
                                conversation_history.append((Current_time, "assistant: " + answer))
                except StopIteration:
                    pass
                except Exception as e:
                    print("An error occurred:", e)
                    break
    else:
        if stream is not None and stream.active:
            stream.stop()
            print("Recording stopped...")
                

listening = False

#include the initialization of the API key, model, and audio recording
def toggle_voice_assistant():
    global listening, stream

    if not listening:
        # Initialize the API key and model when the keybind is hit
        openai.api_key = "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"
        openai.Model.retrieve("text-davinci-002")

    listening = not listening

    if listening:
        print("Voice assistant activated")
        stream = sd.InputStream(device=device_index, samplerate=16000, channels=1, blocksize=1024, callback=callback, dtype=np.float32)
        threading.Thread(target=record_and_transcribe, args=(conn,)).start()
    else:
        if stream is not None and stream.active:
            stream.stop()
            stream.close()  # Add this line to close the input stream
        print("Voice assistant deactivated")


# Initialize the database connection before waiting for the keybind
conn = initialize_database()

keyboard.add_hotkey('ctrl+alt+a', toggle_voice_assistant)
keyboard.wait()