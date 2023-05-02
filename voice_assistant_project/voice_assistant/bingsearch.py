import os
import requests
from dotenv import load_dotenv

load_dotenv()

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

query = "what was the name of the most recent hurricane that hit south florida"
print("question: ", query)
num_results = 8

urls, top_snippet = bing_search(query, num_results=num_results)
if top_snippet:
    print(f"Bing Top Snippet: {top_snippet}\n")
else:
    print("No Bing top snippet found.\n")
print("Retrieved URLs:", urls)
