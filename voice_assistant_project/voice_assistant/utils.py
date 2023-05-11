import queue
import glob
import os
import joblib
import re
import csv
def delete_audio_files():
    audio_files = glob.glob("audio_files/*.wav")
    for audio_file in audio_files:
        try:
            os.remove(audio_file)
            print(f"Deleted: {audio_file}")
        except Exception as e:
            print(f"failed to delete {audio_file}: e")

audio_buffer = queue.Queue() # Create a thread-safe buffer to store audio data

def preprocess_text(text):
    # Lowercase and remove non-alphanumeric characters
    text = re.sub(r'\W+', ' ', text.lower())
    
    return text


def load_model(model_filename, vectorizer_filename):
    with open(model_filename, 'rb') as model_file, open(vectorizer_filename, 'rb') as vectorizer_file:
        model = joblib.load(model_file)
        vectorizer = joblib.load(vectorizer_file)
    return model, vectorizer


def predict_question(model, vectorizer, question):
    question_vector = vectorizer.transform([question])
    prediction = model.predict(question_vector)
    return prediction[0]

def load_data(filename):
    labeled_data = []
    with open(filename, 'r') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader)  # Skip the header row
        for row in datareader:
            question, label = row[0], row[1]
            labeled_data.append((question, label))
    return labeled_data