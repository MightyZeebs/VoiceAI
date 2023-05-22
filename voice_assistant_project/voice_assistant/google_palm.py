import google.generativeai as palm 
from dotenv import load_dotenv
import os

load_dotenv()

palm_api_key = os.getenv("GOOGLE_PALM_API")
palm.configure(api_key=palm_api_key) 
model = 'models/text-bison-001'

def generate_palm_response(query, context_date):
    print("date stuff", context_date)
    context = f"""
    You are google web search but with other AI capabilities. You answer the following questions with the most up to date information around todays date of {context_date}. You provide as much context in an organized manner as possible
    """

    prompt = context + query
    completion = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=.3,
        # The maximum length of the response
        max_output_tokens=800,
    )

    result = completion.result if completion.result else ""
    print("results", result)
    if result.strip():
        return result
    else:
        return None

