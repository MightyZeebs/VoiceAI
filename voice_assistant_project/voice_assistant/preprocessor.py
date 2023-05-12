import os
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn import svm
import pandas as pd
import os

def load_questions():
    # Get current script directory
    current_dir = os.path.dirname(os.path.realpath(__file__))

    # Paths to the question files
    post_2021_questions_path = os.path.join(current_dir, "Test_Train", "questionsPost2021.csv")
    pre_2021_questions_path = os.path.join(current_dir, "Test_Train", "questionsPre2021.csv")

    # Post-2021 questions
    post_2021_questions = pd.read_csv(post_2021_questions_path)
    # Pre-2021 questions
    pre_2021_questions = pd.read_csv(pre_2021_questions_path)
    
    post_2021_questions_list = post_2021_questions['Question'].tolist()
    pre_2021_questions_list = pre_2021_questions['Question'].tolist()

    # Return as a single list of tuples, each with the question and its label
    return [(q, 1) for q in post_2021_questions_list] + [(q, 0) for q in pre_2021_questions_list]

def preprocess_questions(questions):
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform([q[0] for q in questions])
    y = [q[1] for q in questions]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Save the vectorizer
    with open('vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
        
    return X_train, X_test, y_train, y_test

def train_model(X_train, y_train):
    clf = svm.SVC()
    clf.fit(X_train, y_train)

    # Save the model
    with open('model.pkl', 'wb') as f:
        pickle.dump(clf, f)
        
    return clf

def main():
    questions = load_questions()
    X_train, X_test, y_train, y_test = preprocess_questions(questions)
    model = train_model(X_train, y_train)
    print("Model trained and saved")

if __name__ == "__main__":
    main()
