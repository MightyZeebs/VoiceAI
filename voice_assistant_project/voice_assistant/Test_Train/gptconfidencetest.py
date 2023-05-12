from dotenv import load_dotenv
import os
import openai
import datetime

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

def process_user_question(question):
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    prompt = "You are a voice assistant.\nUser: " + question + "\nAssistant:"
    if current_date:
        prompt = "You are a voice assistant.\nSystem: " + current_date + "\nUser: " + question + "\nAssistant:"

    response = openai.Completion.create(
        model="text-davinci-003",  # Use text-davinci-003 model
        prompt=prompt,
        max_tokens=100
    )

    answer = response.choices[0].text.strip()

    print("Generated Answer:", answer)

# Example usage
user_question = "What is the best weapon in Elden Ring?"
process_user_question(user_question)
