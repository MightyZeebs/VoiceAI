import requests
import nltk
import PyPDF2
import os
from bs4 import BeautifulSoup
import spacy
import urllib.parse
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


def google_search(query, num_results=1):
    search_results = []
    featured_snippet = None
    knowledge_panel = None
    try:
        base_url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract featured snippet
        featured_snippet = soup.find("div", class_="xpdopen")
        if featured_snippet:
            featured_snippet = featured_snippet.text

        # Extract knowledge panel
        knowledge_panel = soup.select_one(".kno-rdesc span")
        if knowledge_panel:
            knowledge_panel = knowledge_panel.text

        # Extract search results
        for result in soup.select(".yuRUbf > a"):
            search_results.append(result["href"])
    except Exception as e:
        print(f"Error occurred during Google Search: {e}")

    return search_results, featured_snippet, knowledge_panel

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
        summary_ids = model.generate(inputs['input_ids'], num_beams=6, max_length=1200, early_stopping=True)
        summarized_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        # Generate a second summary with a different range of the text and concatenate
        inputs = tokenizer("summarize: " + text[-1024:], max_length=1024, return_tensors='pt', truncation=True)
        summary_ids = model.generate(inputs['input_ids'], num_beams=6, max_length=1200, early_stopping=True)
        summarized_text2 = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        combined_summary = summarized_text + " " + summarized_text2
        
        summaries.append((url, combined_summary))
        print(f"Generated Summary for URL {idx+1}: {url}\nSummary: {combined_summary}\n")

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
# query = "Ron desantis"
# print("Question: ", query)
# num_results = 8
# keywords = extract_keywords(query)
# print("Extracted keywords: ", keywords)

# # Use Google Search
# urls, featured_snippet, knowledge_panel = google_search(query, num_results=num_results)

# if featured_snippet:
#     print(f"Google Featured Snippet: {featured_snippet}\n")
# else:
#     print("No Google featured snippet found.\n")

# if knowledge_panel:
#     print("Google Knowledge panel:")
#     print(knowledge_panel)
# else:
#     print("No Google knowledge panel found.\n")

# # Use Bing Search
# bing_results, bing_top_snippet = bing_search(query, num_results=num_results)

# if bing_top_snippet:
#     print(f"Bing Top Snippet: {bing_top_snippet}\n")
# else:
#     print("No Bing top snippet found.\n")

# print("Retrieved URLs:", urls)

# text_data = scrape_and_extract_text(urls, max_successful=3)
# print("text data scraped")
# summaries = filter_and_summarize_text(text_data, keywords)
# print("Summaries:")
# for url, summary in summaries:
#     print(f"URL: {url}\nSummary: {summary}\n")


#print("Testing follow-up query:")
# summary_number = 3  # Replace this with the spoken input once integrated with the voice assistant
# follow_up_query(summary_number, summaries, keywords)



#openai integration will be like this 
#def combined_web_search(query):
#     print("Performing web search")
#     bing_results, bing_top_snippet = bing_search(query)
#     google_results, google_featured_snippet, google_knowledge_panel = google_search(query)

#     search_result = ""
#     if google_featured_snippet:
#         print("google snippet: ", google_featured_snippet)
#         search_result += f"Google Featured Snippet: {google_featured_snippet}\n"
#     if google_knowledge_panel:
#         search_result += f"Google Knowledge Panel: {google_knowledge_panel}\n"
#     if bing_top_snippet:
#         print("bing top snippet", bing_top_snippet)
#         search_result += f"Bing Top Snippet: {bing_top_snippet}\n"

#     search_result += "Google URLs:\n"
#     for url in google_results:
#         search_result += f"{url}\n"

#     search_result += "Bing URLs:\n"
#     for url in bing_results:
#         search_result += f"{url}\n"

#     return search_result