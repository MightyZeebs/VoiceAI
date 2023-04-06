import openai
import datetime
from textblob import TextBlob
import datetime
import spacy
import re
from .calender_integration import get_calendar_service, get_date_info, create_reminder
from .database import insert_message, retrieve_database_history, retrieve_memory_history

openai.api_key = "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"
openai.Model.retrieve("gpt-3.5-turbo")

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    doc = nlp(text)
    keywords = [chunk.text for chunk in doc.noun_chunks]
    return keywords

def search_conversation_history(conversation_history, keywords):
    results = []
    for entry in conversation_history:
        if any(keyword.lower() in entry[2].lower() for keyword in keywords):
            results.append(entry)
    return results

def handle_question(question, conversation_history, memory_history, conn, current_time, date_answer):
    current_time = datetime.datetime.now()
    insert_message(conn, current_time, "user", question)

    recall_phrases = ["remember when", "recall", "search for"]
    recall_detected = any(phrase in question.lower() for phrase in recall_phrases)
    
    if recall_detected:
        print("Recall phrase detected")
        keywords = extract_keywords(question)
        print(f"Keywords: {keywords}")
        conversation_history = search_conversation_history(retrieve_database_history(conn, recall=True), keywords)
    else:
        conversation_history = (
            retrieve_memory_history(memory_history, 5)
            if memory_history
            else retrieve_database_history(conn, 5)
        )

    #check for date related question
    doc = nlp(question)
    date_detected = False
    date_keywords = ['date', 'day', 'today', "tomorrow", "yesterday"]
    for token in doc:
        if token.lower_ in date_keywords:
            date_detected = True

    #if question has date entity, use get_date_info
    if date_detected:
        print("date related question")
        try:
            date_info = get_date_info(question)
            if date_info:
                date_answer = date_info
        except Exception as e:
            print(f"Error in date answer: {e}")

    print("conversation history: ", conversation_history)

    history_str = "\n".join(f"{entry[1]}: {entry[2]}" for entry in conversation_history)
    print("conversation history:  ", history_str)
    sentiment = analyze_sentiment(question)
    
    answer = generate_response(question, history_str, sentiment, current_time, date_answer)

    if not answer.strip():
        answer = "I'm sorry, I couldn't understand your question. Please try again."

    conversation_history.append((current_time, "Assistant: " + answer))

    return answer


def analyze_sentiment(input_text):
    blob = TextBlob(input_text)
    sentiment = blob.sentiment.polarity
    return sentiment


def generate_response(input_text, context, sentiment, current_time, date_answer=None):
    emotion = (
        "sad"
        if sentiment < -0.2
        else "happy"
        if sentiment > 0.2
        else "neutral"
    )

    current_date_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    date_info_messsage = f"The date information is: {date_answer}." if date_answer else ""
    system_message = f"Generate a response for a {emotion} user. The current date and time is {current_date_time}. {date_info_messsage}\n{context}\nUser: {input_text}\nAssistant:"
        
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_message}, {"role": "user", "content": input_text}],
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.7,
    )

    answer = response.choices[0].message.content.strip()

    if not answer.strip() or len(answer.split()) < 3:
        print("Emotion-based response didn't work. Trying without emotion...")
        prompt = f"{context}\nUser: {input_text}\nAssistant:"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_message}, {"role": "user", "content": input_text}],
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )

        answer = response.choices[0].message.content.strip()

    return answer

