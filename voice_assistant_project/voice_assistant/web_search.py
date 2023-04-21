import requests
from bs4 import BeautifulSoup
from googlesearch import search
from transformers import T5ForConditionalGeneration, T5Tokenizer
import spacy

nlp = spacy.load("en_core_web_sm")
model = T5ForConditionalGeneration.from_pretrained("t5-small")
tokenizer = T5Tokenizer.from_pretrained("t5-small")

def extract_keywords(text):
    doc = nlp(text)
    keywords = [chunk.text for chunk in doc.noun_chunks] + [token.text for token in doc if token.pos_ == "PROPN"]
    print("keywords:", keywords)
    return keywords

def google_search(query, num_results=1):
    search_results=[]
    try:
        for i, result in enumerate(search(query, lang="en")):
            if i < num_results:
                search_results.append(result)
            else:
                break
    except Exception as e:
        print(f"Error occurred during Google Search: {e}")
    return search_results

def scrape_and_extract_text(urls, max_successful=3):
    text_data = []
    successful_scrapes = 0
    for url in urls:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            # extract text from paragraph tags
            paragraphs = soup.find_all("p")
            if paragraphs:
                successful_scrapes += 1
                print(f"Successfully scraped URL {successful_scrapes}: {url}")
                for p in paragraphs:
                    text_data.append((url, p.get_text()))

        except Exception as e:
            print(f"Error occurred during web scraping: {e}")
        if successful_scrapes >= max_successful:
            break
    return text_data


def filter_and_summarize_text(text_data, keywords):
    summaries = []
    for idx, (url, text) in enumerate(text_data):
        for keyword in keywords:
            if keyword.lower() in text.lower():
                inputs = tokenizer("summarize: " + text, max_length=1024, return_tensors='pt', truncation=True)
                summary_ids = model.generate(inputs['input_ids'], num_beams=4, max_length=150, early_stopping=True)
                summarized_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

                if any(kw in summarized_text for kw in keywords):
                    summaries.append((url, summarized_text))  # Changed this line
                    print(f"Generated Summary for URL {idx+1}: {url}\nSummary: {summarized_text}\n")
                    break
    return summaries

# Test the functionality of the code
query = "what is the best faith based weapon in elden ring"
print("question", query)
num_results = 8
keywords = extract_keywords(query)
print("Extracted keywords: ", keywords)
urls = google_search(query, num_results=num_results)
print("Retrieved URLs:", urls)
text_data = scrape_and_extract_text(urls, max_successful=3)
print("text data scraped")
summaries = filter_and_summarize_text(text_data, keywords)
print("Summaries:")
for url, summary in summaries:
    print(f"URL: {url}\nSummary: {summary}\n")