import requests

from bs4 import BeautifulSoup
from googlesearch import search
from transformers import BartTokenizer, BartForConditionalGeneration

def google_search(query, num_results=5):
    search_results=[]
    try:
        for result in search(query, num_results=num_results, lang="en", safe="off"):
            search_results.append(result)
    except Exception as e:
        print(f"Error occurred during Google Search: {e}")
    return search_results

def scrape_and_extract_text(urls):
    text_data=[]
    for url in urls:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            #extract text from parargraph tags
            paragraphs = soup.find_all("p")
            for p in paragraphs:
                text_data.append(p.get_text())

        except Exception as e:
            print(f"Error occured during web scraping: {e}")
    return text_data

from transformers import BartTokenizer, BartForConditionalGeneration

def summarize_text(text):
    model_name = "facebook/bart-large-cnn"
    tokenizer = BartTokenizer.from_pretrained(model_name)
    model = BartForConditionalGeneration.from_pretrained(model_name)

    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = model.generate(inputs["input_ids"], num_beams=4, max_length=100, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return summary
