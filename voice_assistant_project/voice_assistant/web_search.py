import requests
from bs4 import BeautifulSoup
from googlesearch import search
from gensim.summarization import summarize

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

def summarize_text(text_data, keywords):
    summary = []

    for text in text_data:
        sumarized_text = summarize(text)
        if summarized_text:
                summary.append(text)
    return summary
