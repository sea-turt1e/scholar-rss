from serpapi import GoogleSearch

params = {
    "engine": "google_scholar",
    "q": "AI",
    "api_key": "API_KEY",
}

search = GoogleSearch(params)
results = search.get_dict()
organic_results = results["organic_results"]
