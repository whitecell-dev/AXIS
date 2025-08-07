from calyx.core import RuleEngine, validate
import requests, time, os

API_KEY = os.getenv("VISUAL_CROSSING_KEY")
BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
CACHE_TTL = 60 * 60 * 12
cache = {}

# ---- Simple rule engine (only calls fetch_weather) ----
class WeatherEngine(RuleEngine):
    def run(self, input_data: dict) -> dict:
        # Validate first
        is_valid, errors = validate(input_data, {"city": "str"})
        if not is_valid:
            return {"error": errors[0]}
        return fetch_weather(input_data)

# ---- Weather fetch function with cache ----
def fetch_weather(input_data):
    city = input_data["city"].lower()
    if city in cache:
        if time.time() - cache[city]["timestamp"] < CACHE_TTL:
            return cache[city]["data"]
    try:
        url = f"{BASE_URL}/{city}?unitGroup=metric&key={API_KEY}&contentType=json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        cache[city] = {"timestamp": time.time(), "data": data}
        return data
    except Exception as e:
        return {"error": str(e)}

# ---- Launch server ----
if __name__ == "__main__":
    engine = WeatherEngine({"rules": []})  # rules not needed
    engine.serve(port=8080)

