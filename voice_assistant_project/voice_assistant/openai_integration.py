import openai
import datetime
from textblob import TextBlob

from .database import insert_message, retrieve_database_history, retrieve_memory_history

openai.api_key = "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"
openai.Model.retrieve("gpt-3.5-turbo")


def handle_question(question, conversation_history, memory_history, conn):
    current_time = datetime.datetime.now()
    insert_message(conn, current_time, "user", question)

    conversation_history = (
        retrieve_memory_history(memory_history, 5)
        if memory_history
        else retrieve_database_history(conn, 5)
    )

    recall_phrases = ["remember when", "recall", "search for"]
    first_words = " ".join(question.lower().split()[:3])

    filtered_history = (
        conversation_history
        if any(first_words.startswith(phrase) for phrase in recall_phrases)
        else [
            entry
            for entry in conversation_history
            if (current_time - entry[0]) <= datetime.timedelta(minutes=5)
        ]
    )

    history_str = "\n".join(f"{entry[1]}: {entry[2]}" for entry in filtered_history)
    sentiment = analyze_sentiment(question)
    answer = generate_response(question, history_str, sentiment)

    if not answer.strip():
        answer = "I'm sorry, I couldn't understand your question. Please try again."

    conversation_history.append((current_time, "Assistant: " + answer))

    return answer


def analyze_sentiment(input_text):
    blob = TextBlob(input_text)
    sentiment = blob.sentiment.polarity
    return sentiment


def generate_response(input_text, context, sentiment):
    emotion = (
        "sad"
        if sentiment < -0.2
        else "happy"
        if sentiment > 0.2
        else "neutral"
    )

    system_message = f"Generate a response for a {emotion} user.\n{context}\nUser: {input_text}\nAssistant:"
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

