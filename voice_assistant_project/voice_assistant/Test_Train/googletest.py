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


# def answer(q):
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
#     }
#     response = requests.get(
#         f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}",
#         headers=headers
#     )
#     soup = BeautifulSoup(response.content, "html.parser")

#     # Select elements similar to the JavaScript function
#     kp_header = soup.select(".kp-header [data-md]")
#     kCrYT = soup.select(".kCrYT")
#     data_async_token = soup.select("[data-async-token]")
#     el = soup.select_one("[id*='lrtl-translation-text']") \
#         or (kp_header[1] if len(kp_header) > 1 else None) \
#         or (kCrYT[1] if len(kCrYT) > 1 else None) \
#         or next((element for element in soup.select("*") if "Calculator Result" in element.text), None) \
#         or next((element for element in soup.select("*") if "Featured snippet from the web" in element.text or "Description" in element.text or "Calculator result" in element.text), None) \
#         or soup.select_one(".card-section, [class*='__wholepage-card'] [class*='desc']") \
#         or soup.select_one(".thODed") \
#         or (data_async_token[-1] if len(data_async_token) > 0 else None) \
#         or soup.select_one("miniapps-card-header") \
#         or soup.select_one("#tw-target")

#     if el:
#         text = el.text.strip()
#         if "translation" in text and "Google Translate" in text:
#             text = text.split("Verified")[0].trim()
#         if "Calculator Result" in text and "Your calculations and results" in text:
#             text = text.split("them")[1].split("(function()")[0].split("=")[1].trim()
#         return text

#     # Sleep for a random interval between requests
#     time.sleep(random.uniform(1, 5))


#     # Sleep for a random interval between requests
#     time.sleep(random.uniform(1, 5))

# # Test the functionality of the code
# query = "Ron Desantis most recent law"
# print("Question: ", query)

# response = answer(query)
# if response:
#     print(f"Response: {response}\n")
# else:
#     print("No response found.\n")