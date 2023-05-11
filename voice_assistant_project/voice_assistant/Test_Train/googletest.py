import requests
import random
import time
import nltk
import PyPDF2
import os
import urllib.parse
from bs4 import BeautifulSoup
import spacy
from dotenv import load_dotenv
from io import BytesIO
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import BartForConditionalGeneration, BartTokenizer


def google_search(query):
    featured_snippet = None
    try:
        base_url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the featured snippet from the search results
        featured_snippet_container = soup.find("div", class_="xpdopen")
        if featured_snippet_container:
            featured_snippet = featured_snippet_container.get_text()

    except Exception as e:
        print(f"Error occurred during Google Search: {e}")
    
    # Sleep for a random interval between requests
    time.sleep(random.uniform(1, 5))

    return featured_snippet

# Test the functionality of the code
query = "When was the most recent earthquake in California"
print("Question: ", query)

featured_snippet = google_search(query)
if featured_snippet:
    print(f"Featured Snippet: {featured_snippet}\n")
else:
    print("No featured snippet found.\n")