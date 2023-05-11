import joblib
import os
import re
import pickle

os.chdir('C:\\Users\\Zeebra\\code\\VoiceAI\\Model')

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

def main():
    model_filename = 'QuestionClassificationModel.pkl'
    vectorizer_filename = 'Vectorizer.pkl'
    model, vectorizer = load_model(model_filename, vectorizer_filename)

    question = "where do i find that?"
    
    prediction = predict_question(model, vectorizer, question)
    if prediction == 'post-2021':
        print(f"Web search needed: {question}")
    else:
        print(f"Question: {question}")

if __name__ == "__main__":
    main()
