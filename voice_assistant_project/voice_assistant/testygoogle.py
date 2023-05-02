from bs4 import BeautifulSoup
import requests, lxml

params = {
    "q": "what was the last hurricane to hit south florida",
    "hl": "en",  # language
    "gl": "us"   # country of the search, US -> USA
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
}

html = requests.get("https://www.google.com/search", params=params, headers=headers, timeout=30)
soup = BeautifulSoup(html.text, "lxml")

# Featured snippet
featured_snippet = soup.select_one("span.ILfuVd span.hgKElc")

# Knowledge panel
knowledge_panel = soup.select_one(".kno-rdesc span")

if featured_snippet:
    print("Featured snippet:")
    print(featured_snippet.text)
else:
    print("No featured snippet found.")

print("\n")

if knowledge_panel:
    print("Knowledge panel:")
    print(knowledge_panel.text)
else:
    print("No knowledge panel found.")


