import requests

class NutritionWrapper:
    def __init__(self, api_key: str):
        self.base_url = "https://api.calorieninjas.com/v1/nutrition"
        self.headers = {'X-Api-Key': api_key}

    def nutrition_analysis(self, query: str) -> dict:
        print(f"Querying nutrition info for: '{query}'")
        response = requests.get(self.base_url, params={'query': query}, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Wrapper API error: {response.status_code}")
            return None