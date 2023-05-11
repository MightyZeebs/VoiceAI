import csv
import random
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report
import pickle
from utils import load_model, load_data, preprocess_text, predict_question


# Load datasets
post_2021_data = load_data('C:\\Users\\Zeebra\\code\\VoiceAI\\voice_assistant_project\\voice_assistant\\Test_Train\\questionsPost2021.csv')
pre_2021_data = load_data('C:\\Users\\Zeebra\\code\\VoiceAI\\voice_assistant_project\\voice_assistant\\Test_Train\\questionsPre2021.csv')

# Combine and shuffle datasets
labeled_data = post_2021_data + pre_2021_data
random.shuffle(labeled_data)

# Split into questions and labels
questions, labels = zip(*labeled_data)

# Preprocess and tokenize the data
vectorizer = TfidfVectorizer(stop_words='english', preprocessor=preprocess_text)
X = vectorizer.fit_transform(questions)

# Split the data into training and validation sets
X_train, X_val, y_train, y_val = train_test_split(X, labels, test_size=0.2, random_state=42)

# Train a Naive Bayes classifier
clf = MultinomialNB(alpha=0.1)
clf.fit(X_train, y_train)

# Save the model and vectorizer
with open("C:\\Users\\Zeebra\\code\\VoiceAI\\voice_assistant_project\\voice_assistant\\model\\model.pkl", "wb") as f:
    pickle.dump(clf, f)

with open("C:\\Users\\Zeebra\\code\\VoiceAI\\voice_assistant_project\\voice_assistant\\model\\vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

# Evaluate the classifier's performance on the validation set
y_pred = clf.predict(X_val)
accuracy = accuracy_score(y_val, y_pred)
print("Accuracy: {:.2f}".format(accuracy * 100))
print(classification_report(y_val, y_pred, zero_division=0))




