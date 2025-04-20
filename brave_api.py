import requests


class BraveApi:

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key must be provided during BraveApi initialization.")
        self.api_key = api_key
        self.api_endpoint = "https://api.search.brave.com/res/v1/web/search"


    def search(self, query: str, count: int = 10) -> list[dict[str, str]] | None:
        if not query: return None
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        params = {"q": query, "count": count}
        
        try:
            response = requests.get(self.api_endpoint, params=params, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            search_results_json = response.json()
            
            results_list = []
            if search_results_json.get("web") and search_results_json["web"].get("results"):
                for result in search_results_json["web"]["results"]:
                    results_list.append({
                        "title": result.get("title", "No Title"),
                        "url": result.get("url", "#"),
                        "description": result.get("description", "No Description")
                    })
            
            return results_list
        
        except Exception as e:
            print(f"An unexpected error occurred during Brave API search: {e}")
            return None
