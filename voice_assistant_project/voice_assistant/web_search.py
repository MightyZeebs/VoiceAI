import requests
from bs4 import BeautifulSoup
from googlesearch import search
from transformers import BartForConditionalGeneration, BartTokenizer

# Load the BART model and tokenizer
model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")

def google_search(query, num_results=1):
    search_results=[]
    try:
        for i, result in enumerate(search(query, lang="en", safe="off")):
            if i < num_results:
                search_results.append(result)
            else:
                break
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

def summarize_text(text_data, keywords):
    summary = []
    for text in text_data:
        inputs = tokenizer([text], max_length=1024, return_tensors='pt', truncation=True)
        summary_ids = model.generate(inputs['input_ids'], num_beams=4, max_length=150, early_stopping=True)
        summarized_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        for keyword in keywords:
            if keyword in summarized_text:
                summary.append(summarized_text)
                break
    print("Summary of URLs:", summary)
    return summary

# Test the functionality of the code
query = "does chick fil a supports anti gay rhetoric"
num_results = 1
keywords = ["Chick fil a", "gay", "support"]
urls = google_search(query, num_results=num_results)
print("Retrieved URLs:", urls)
text_data = scrape_and_extract_text(urls)
summaries = summarize_text(text_data, keywords)
print("Summaries:", summaries)