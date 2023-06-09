import openai
import os
import datetime
import re
import spacy
import pickle
import joblib
from dotenv import load_dotenv
from .calender_integration import get_calendar_service, get_date_info, create_reminder
from .database import insert_message, retrieve_database_history
from .nlp_processing import extract_keywords, search_conversation_history, remove_duplicates
from .web_search import bing_search, google_search
from sklearn.feature_extraction.text import CountVectorizer
from textblob import TextBlob
from .google_palm import generate_palm_response

current_dir = os.path.dirname(os.path.abspath(__file__))

nlp = spacy.load("en_core_web_sm")

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "model.pkl")
vectorizer_path = os.path.join(current_dir, "vectorizer.pkl")
conversation_history = []
model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)
reset_timestamp = None #variable timestamp for ignoring all database chat history from before this button 

def handle_question(question, conn, current_time, ui):
    global reset_timestamp, conversation_history
    current_time = datetime.datetime.now()
    print(type(conn))
    print(type(current_time))
    print(f"conn is: {conn}")

    recall_phrases = ["remember when", "recall", "search for"]
    recall_detected = any(phrase in question.lower() for phrase in recall_phrases)

    if recall_detected:
        print("Recall phrase detected")
        keywords = extract_keywords(question, recall_phrases)
        print(f"Keywords: {keywords}")
        conversation_history = search_conversation_history(retrieve_database_history(conn, recall=True), keywords)
    elif "reset chat" in question.lower():
        reset_timestamp = current_time  # Update the reset timestamp when the chat is reset
        conversation_history = []  # Reset conversation_history
        ui.clear_chat_box()  # Clear the chatbox in the UI
        return "Chat has been successfully reset."
    else:
        insert_message(conn, current_time, "user", question)
        conversation_history = retrieve_database_history(conn, reset_timestamp=reset_timestamp, max_messages=6)
    
    #check for date related question
    doc = nlp(question)
    date_detected = False
    date_answer = None
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
    #print("Unique conversation history: ", unique_conversation_history)
    history_str = "\n".join(f"{entry[1]}: {entry[2]}" for entry in unique_conversation_history)
    print("history_str:  ", history_str)
    sentiment = analyze_sentiment(question)

    requires_web_search = False

    if len(conversation_history) <= 1:
        print("checking for web search question")
        question_vector = vectorizer.transform([question])
        requires_web_search = model.predict(question_vector)[0]
    elif "web search needed" in question.lower() or ui.app.assistant.force_web_search:
        requires_web_search = True

    # If the model predicts that the question requires post-2021 knowledge, trigger web search
    if requires_web_search:
        print("Web search required")
        # Generate a new query using OpenAI
        new_query = generate_web_search_query(question, history_str)
        
        # Pass the new query to your web search function
        search_result = combined_web_search(new_query, current_time)
        
        # Send the search result back to OpenAI for a final response
        answer = generate_response(question, history_str, sentiment, current_time, date_answer, search_result)
        insert_message(conn, current_time, "assistant", answer)
        return answer 
    else:
        print("Web search not required")

    print("generating response")
    answer = generate_response(question, history_str, sentiment, current_time, date_answer)

    if not answer.strip():
        answer = "I'm sorry, I couldn't understand your question. Please try again."
    else:
        insert_message(conn, current_time, "assistant", answer)
        unique_conversation_history.append((current_time, "Assistant: " + answer))

    return answer

def combined_web_search(query, current_time):
    print("Performing web search")

    # First, try to get a response from PALM
    palm_context = generate_palm_response(query)
    if palm_context:
        # If PALM returned a result, return it immediately
        return palm_context
    
    # If PALM didn't return a result, fall back to Bing and Google searches
    bing_results, bing_top_snippet = bing_search(query)
    google_results, google_featured_snippet, google_knowledge_panel = google_search(query)

    search_result = ""
    if google_featured_snippet:
        print("google snippet: ", google_featured_snippet)
        search_result += f"Google Featured Snippet: {google_featured_snippet}\n"
    if google_knowledge_panel:
        search_result += f"Google Knowledge Panel: {google_knowledge_panel}\n"
    if bing_top_snippet:
        print("bing top snippet", bing_top_snippet)
        search_result += f"Bing Top Snippet: {bing_top_snippet}\n"

    search_result += "Google URLs:\n"
    for url in google_results:
        search_result += f"{url}\n"

    search_result += "Bing URLs:\n"
    for url in bing_results:
        search_result += f"{url}\n"

    return search_result

def analyze_sentiment(input_text):
    print("analyzing sentiment")
    blob = TextBlob(input_text)
    sentiment = blob.sentiment.polarity
    print ("sentiement: ", sentiment)
    return sentiment

def generate_web_search_query(input_text, context):
    print("Generating web search query...")
    system_message = "Do not answer the question. Instead you will combine the conversation history and most recent query to generate a new query that simplifies the question. Only respond with the new query"
    
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "assistant", "content": context},
                {"role": "user", "content": f"Transform this question into a web search query: '{input_text}'"}
            ],
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.1,
        )
    except openai.error.RateLimitError:
        print("RateLimitError: Model is currently overloaded with requests. Please try again later.")
        return "Apologies, I'm currently a bit busy. Could you please try again in a few moments?"


    new_query = response.choices[0].message.content.strip()
    print("new query: ", new_query)
    return new_query


def generate_response(input_text, context, sentiment, current_time, date_answer=None, search_result=None):
    print("Generating response based on input and context...")
    emotion = (
        "sad"
        if sentiment < -0.2 
        else "happy"
        if sentiment > 0.2
        else "neutral"
    )

    current_date_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    date_info_messsage = f"The date information is: {date_answer}." if date_answer else ""
    system_message = f"Generate a response as a helpful human-like assistant with a distinct personality. Be honest, inquisitive, and occasionally use humor, excitement, and sarcasm (about 20% of the time). Your knowledge is up to September 2021, and you should not guess or lie about any information. The current date and time is {current_date_time}. {date_info_messsage}"
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": input_text}
    ]

    if search_result:
        search_message = f"System to=assistant code: Please use the following information to answer the user's question. {search_result}"
        messages.append({"role": "system", "content": search_message})
    
    try:   
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=400,
            n=1,
            stop=None,
            temperature=0.5,
        )

    except openai.error.RateLimitError:
        print("RateLimitError: Model is currently overloaded with requests. Please try again later.")
        return "Apologies, I'm currently a bit busy. Could you please try again in a few moments?"


    answer = response.choices[0].message.content.strip()



    if not answer.strip() or len(answer.split()) < 3:
        print("Emotion-based response didn't work. Trying without emotion...")
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": system_message}, {"role": "user", "content": input_text}],
               max_tokens=200,
                n=1,
                stop=None,
                temperature=0.5,
            )
        except openai.error.RateLimitError:
            print("RateLimitError: Model is currently overloaded with requests. Please try again later.")
            return "Apologies, I'm currently a bit busy. Could you please try again in a few moments?"

        answer = response.choices[0].message.content.strip()

    return answer