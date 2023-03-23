import io
import queue
import sounddevice as sd
import sys
import time
import numpy as np
import soundfile as sf
import openai
import sqlite3
import datetime
from google.cloud import speech # Import the Google Cloud client library

openai.api_key = "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"
openai.Model.retrieve("text-davinci-002")

audio_buffer = queue.Queue()
    # Create a thread-safe buffer to store audio data

conversation_history = []

def create_connection():
    #create a connection to the SQLite database
    conn = None
    try:
        conn = sqlite3.connect('conversation_history.db')
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

conn = create_connection()
create_table(conn)

def insert_message(conn, timestamp, speaker, text):
    #insert a message into the conversation history table
    try:
        c = conn.cursor()
        c.execute(f"INSERT INTO conversation_history (timestamp, speaker, text) VALUES (?, ?, ?)",
                  (timestamp, speaker, text))
        conn.commit()
        print('Successfully inserted message into conversation history.')
    except sqlite3.Error as e:
        print(e)
    
def retrieve_conversation_history(conn, minutes=5):
    #retrieve the conversation history from the database
    current_time = datetime.datetime.now()
    time_threshold = current_time - datetime.timedelta(minutes=minutes)
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM conversation_history WHERE timestamp >= ?", (time_threshold))
        rows = c.fetchall()
        return rows if rows else [] # return an empty list if rows is empty
    except sqlite3.Error as e:
        print(e)
        
def callback(indata, frames, time, status):
    # Define a callback function to handle audio data
    if status:
        print(status, file=sys.stderr)
    audio_buffer.put((indata.copy() * np.iinfo(np.int16).max).astype(np.int16))

def handle_question(question, conversation_history, conn):
    #Define how to the AI handles questions and understands previous context
    current_time = datetime.datetime.now()
    insert_message(conn, current_time, "user", question)

    if not conversation_history:
        conversation_history = retrieve_conversation_history(conn, 5)
    
    filtered_history = [
        entry for entry in conversation_history
        if (current_time - entry[0]) <= datetime.timedelta(minutes=5)
    ]

    if len(filtered_history) < 2 or len(filtered_history[-2][1]) < 2:
        context = ""
    else:
        context = filtered_history[-2][-1]

    follow_up_phrases = ["also", "follow up", "continue about", "continue with"]
    if any(phrase in question.lower() for phrase in follow_up_phrases) or len(filtered_history) >= 2:
            #use the previous question as context
            context = filtered_history[-2][-1]
            prompt = f"{context}\nAssistant:"
    else:
        #Use entire conversation history as context
        history_str = "\n".join(entry[1] for entry in filtered_history)
        prompt = f"{history_str}\nAssistant:"

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

print("Conversation history:", conversation_history)

def record_and_transcribe(conn, duration):
    # The record_and_transcribe function takes a duration (in seconds)
    # It records audio input from the user for the specified duration, transcribes it using Google Cloud Speech-to-Text,
    # and passes the transcribed text to OpenAI API for generating a response based on the conversation history.
  
    client = speech.SpeechClient()
      # Create a Google Cloud Speech-to-Text client to handle speech recognition

    config = speech.RecognitionConfig(
        # Configure the speech recognition settings
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US"
    )
  
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=False #only get the final results
    )

    def get_microphone_index():
        #get the microphone index
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

    def audio_generator():
        # Create a generator that yields audio chunks
        stream = sd.InputStream(device=device_index, samplerate=16000, channels=1, blocksize=1024, callback=callback, dtype=np.float32)
        stream.start()
        print("Recording started...")

        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                try:
                    data = audio_buffer.get(timeout=1)
                    #print("Data length:", len(data))
                    audio_request = speech.RecognitionAudio(content=data.tobytes())
                    yield speech.StreamingRecognizeRequest(audio_content=audio_request.content)
                except queue.Empty:
                    pass
        finally:
            stream.stop()
            stream.close()            
            print("Recording finished...")
        
    requests = audio_generator()
    responses = client.streaming_recognize(streaming_config, requests=requests)

    # Process the responses
    for response in responses:
        if not response.results:
            print("No transcription results found.")
        else:
            # only print the final result
            result = response.results[-1]
            if result.is_final:
                transcript = result.alternatives[0].transcript
                print("user:", transcript)

                Current_time = datetime.datetime.now()
                insert_message(conn, str(Current_time), "user", transcript)

                answer = handle_question(transcript, conversation_history, conn)
                print("assistant:", answer)

                Current_time = datetime.datetime.now()
                insert_message(conn, str(Current_time), "assistant", answer)
                insert_message(conn, str(Current_time), "user", transcript)
                conversation_history.append((Current_time, "assistant: " + answer))
                    #update assistant with previous questions
                
record_and_transcribe(conn, duration=10)
 # Record for 10 seconds

