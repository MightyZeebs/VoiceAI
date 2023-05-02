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

load_dotenv()
nlp = spacy.load("en_core_web_sm")
model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
nltk.download('stopwords')
stop_words = set(stopwords.words("english"))

def extract_keywords(text, top_n=10):
    doc = nlp(text)
    tokens = [token.text for token in nlp(text) if token.text.lower() not in stop_words and not token.is_punct]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([" ".join(tokens)])
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = tfidf_matrix.toarray().flatten()
    sorted_indices = tfidf_scores.argsort()[::-1][:top_n]
    keywords = [feature_names[i] for i in sorted_indices]
    print("keywords:", keywords)
    return keywords

def bing_search(query, num_results=1):
    search_results = []
    top_snippet = None
    try:
        api_key = os.environ.get("BING_API_KEY")
        base_url = "https://api.bing.microsoft.com/v7.0/search"
        
        headers = {
            "Ocp-Apim-Subscription-Key": api_key
        }
        params = {
            "q": query,
            "count": num_results,
            "responseFilter": "Webpages"
        }
        
        response = requests.get(base_url, headers=headers, params=params)
        print(f"Response code: {response.status_code}")
        data = response.json()
        print(f"Response data: {data}")

        # Get search results
        search_results = data.get("webPages", {}).get("value", [])

        # Extract the snippet from the top search result
        if search_results:
            top_snippet = search_results[0]['snippet']

    except Exception as e:
        print(f"Error occurred during Bing Search: {e}")
    return search_results, top_snippet

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
        featured_snippet_container = soup.find("div", class_="BNeawe s3v9rd AP7Wnd")
        if featured_snippet_container:
            featured_snippet = featured_snippet_container.get_text()

    except Exception as e:
        print(f"Error occurred during Google Search: {e}")
    
    # Sleep for a random interval between requests
    time.sleep(random.uniform(1, 5))

    return featured_snippet

# Test the functionality of the code
query = "what was the name of the most recent hurricane that hit south florida"
print("Question: ", query)

featured_snippet = google_search(query)
if featured_snippet:
    print(f"Featured Snippet: {featured_snippet}\n")
else:
    print("No featured snippet found.\n")



def scrape_and_extract_text(urls, max_successful=3):
    text_data = []
    successful_scrapes = 0
    for url in urls:
        response = requests.get(url, timeout=8)
        if response.headers['content-type'] == 'application/pdf':
            print(f"Attempting to extract text from PDF URL: {url}")
            pdf_text = extract_text_from_pdf(url)
            if pdf_text:
                successful_scrapes += 1
                print(f"Successfully extracted text from PDF URL {successful_scrapes}: {url}")
                text_data.append((url, pdf_text))
            continue
        print(f"Attempting to scrape URL {successful_scrapes + 1}: {url}")
        try:
            soup = BeautifulSoup(response.content, "html.parser")

            # extract text from paragraph tags
            paragraphs = soup.find_all("p")
            if paragraphs:
                successful_scrapes += 1
                print(f"Successfully scraped URL {successful_scrapes}: {url}")
                url_text = " ".join([p.get_text() for p in paragraphs])
                text_data.append((url, url_text))

        except Exception as e:
            print(f"Error occurred during web scraping: {e}")
        print(f"Finished processing URL {successful_scrapes + 1}: {url}\n") 
        if successful_scrapes >= max_successful:
            break
    return text_data



def filter_and_summarize_text(text_data, keywords, max_summaries=3):
    # Calculate the relevance score for each URL
    relevance_scores = []
    for idx, (url, text) in enumerate(text_data):
        keyword_count = sum(2 if kw.lower() in text.lower() else 0 for kw in keywords)
        relevance_scores.append((url, text, keyword_count))

    # Sort the URLs based on their relevance scores
    sorted_urls = sorted(relevance_scores, key=lambda x: x[2], reverse=True)

    # Generate summaries for the top max_summaries URLs
    summaries = []
    for idx, (url, text, _) in enumerate(sorted_urls[:max_summaries]):
        inputs = tokenizer("summarize: " + text, max_length=1024, return_tensors='pt', truncation=True)
        summary_ids = model.generate(inputs['input_ids'], num_beams=6, max_length=800, early_stopping=True)
        summarized_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summaries.append((url, summarized_text))
        print(f"Generated Summary for URL {idx+1}: {url}\nSummary: {summarized_text}\n")

    return summaries

def extract_text_from_pdf(url):
    try:
        response = requests.get(url, timeout=10)
        with BytesIO(response.content) as pdf_content:
            pdf_reader = PyPDF2.PdfFileReader(pdf_content)
            num_pages = min(pdf_reader.numPages, 5)  # Limit the number of pages to process
            text_data = ""
            for page_number in range(num_pages):
                page = pdf_reader.getPage(page_number)
                text_data += page.extractText()
        return text_data
    except Exception as e:
        print(f"Error occurred during PDF text extraction: {e}")
        return None
    

# def follow_up_query(summary_number, summaries, keywords):
#     if summary_number > 0 and summary_number <= len(summaries):
#         selected_summary = summaries[summary_number - 1]
#         print(f"Following up on summary {summary_number}: {selected_summary[1]}\n")
#         new_query = selected_summary[1]
#     else:
#         print("Invalid summary number. Please provide a valid summary number.")
#         return

#     # Perform the entire process again with the new query
#     print("New query:", new_query)
#     new_keywords = extract_keywords(new_query)
#     print("New extracted keywords: ", new_keywords)
#     combined_keywords = list(set(keywords + new_keywords))
#     print("Combined keywords:", combined_keywords)
#     new_urls = google_search(new_query, num_results=num_results)
#     print("New retrieved URLs:", new_urls)
#     new_text_data = scrape_and_extract_text(new_urls, max_successful=3)
#     print("New text data scraped")
#     new_summaries = filter_and_summarize_text(new_text_data, combined_keywords)
#     print("New summaries:")
#     for url, summary in new_summaries:
#         print(f"URL: {url}\nSummary: {summary}\n")

# Test the functionality of the code
# Test the functionality of the code
query = "what was the name of the most recent hurricane that hit south florida"
print("question: ", query)
num_results = 8
# keywords = extract_keywords(query)
# print("Extracted keywords: ", keywords)


# Update the code to handle the Bing top snippet
# Update the code to scrape Google search instead of using the Custom Search API
featured_snippet = google_search(query)
if featured_snippet:
    print(f"Featured Snippet: {featured_snippet}\n")
else:
    print("No featured snippet found.\n")


# text_data = scrape_and_extract_text(urls, max_successful=3)
# print("text data scraped")
# summaries = filter_and_summarize_text(text_data, keywords)
# print("Summaries:")
# for url, summary in summaries:
#     print(f"URL: {url}\nSummary: {summary}\n")

#print("Testing follow-up query:")
# summary_number = 3  # Replace this with the spoken input once integrated with the voice assistant
# follow_up_query(summary_number, summaries, keywords)