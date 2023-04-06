import openai
import datetime
from textblob import TextBlob
import datetime
import spacy
import re
from spacy.matcher import PhraseMatcher
from .calender_integration import get_calendar_service, get_date_info, create_reminder
from .database import insert_message, retrieve_database_history, retrieve_memory_history

openai.api_key = "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"
openai.Model.retrieve("gpt-3.5-turbo")

nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")


import spacy
from spacy.matcher import PhraseMatcher
from spacy.lang.en.stop_words import STOP_WORDS

nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

def extract_keywords(text, recall_phrases):
    # If using all conversation, extracts keywords to search with for context
    stop_phrases_patterns = [nlp(phrase) for phrase in recall_phrases]
    matcher.add("StopPhrases", stop_phrases_patterns)

    doc = nlp(text)
    print(f"doc: {doc}")
    matches = matcher(doc)
    for match_id, start, end in matches:
        for token in doc[start:end]:
            token.set_extension("is_stop_phrase", default=False, force=True)
            token._.is_stop_phrase = True

    keywords = []

    for chunk in doc.noun_chunks:
        print(f"chunk: {chunk}")
        token = chunk.text.lower()
        if token not in STOP_WORDS and chunk.root.pos_ != "PRON" and not any(tok._.is_stop_phrase for tok in chunk):  # Remove pronouns and stop phrases
            if not keywords:
                for token in doc:
                    if token.pos_ =="NOUN" and not token.is_stop and token.text.lower() not in [phrase.lower() for phrase, in recall_phrases]:
                        keywords.append(token.text.lower())
            print(f"Adding keyword: {token}")
            keywords.append(token)

    # Remove duplicates and limit keywords
    unique_keywords = list(set(keywords))
    max_keywords = 5
    return unique_keywords[:max_keywords]

def search_conversation_history(conversation_history, keywords):
    #searches entire databse for those keywords
    results = []
    for entry in conversation_history:
        if any(keyword.lower() in entry[2].lower() for keyword in keywords) and entry not in results:
            results.append(entry)
    return results

def remove_duplicates(conversation_history):
    unique_history = []
    content_set = set()
    for entry in conversation_history:
        content = entry[2]
        if content not in content_set:
            unique_history.append(entry)
            content_set.add(content)
    return unique_history

def handle_question(question, conversation_history, memory_history, conn, current_time, date_answer):
    current_time = datetime.datetime.now()
    insert_message(conn, current_time, "user", question)

    recall_phrases = ["remember when", "recall", "search for"]
    recall_detected = any(phrase in question.lower() for phrase in recall_phrases)
    
    if recall_detected:
        print("Recall phrase detected")
        keywords = extract_keywords(question, recall_phrases)
        print(f"Keywords: {keywords}")
        conversation_history = search_conversation_history(retrieve_database_history(conn, recall=True), keywords)      
    else:
        conversation_history = (
            retrieve_memory_history(memory_history, 5)
            if memory_history
            else retrieve_database_history(conn, minutes=5)
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

    unique_conversation_history = remove_duplicates(conversation_history)

    print("Unique conversation history: ", unique_conversation_history)

    history_str = "\n".join(f"{entry[1]}: {entry[2]}" for entry in unique_conversation_history)
    print("history_str:  ", history_str)
    sentiment = analyze_sentiment(question)
    
    answer = generate_response(question, history_str, sentiment, current_time, date_answer)

    if not answer.strip():
        answer = "I'm sorry, I couldn't understand your question. Please try again."

    unique_conversation_history.append((current_time, "Assistant: " + answer))

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
    system_message = f"Generate a response for a {emotion} user. Use humor and sarcasm when appropriate. The current date and time is {current_date_time}. {date_info_messsage}\n{context}\nUser: {input_text}\nAssistant:"
        
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_message}, {"role": "user", "content": input_text}],
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
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
            temperature=0.5,
        )

        answer = response.choices[0].message.content.strip()

    return answer

