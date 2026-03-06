import requests
import datetime
import json
from config import OPENWEATHER_API_KEY, OPENROUTER_API_KEY, SEARCHAPI_API_KEY

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        resp = requests.get(url)
        data = resp.json()
        if data.get("cod") != 200:
            return None
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"{temp}°C, {desc}"
    except:
        return None

def generate_greeting(name, city):
    hour = datetime.datetime.now().hour
    if hour < 12:
        tod = "morning"
    elif hour < 18:
        tod = "afternoon"
    else:
        tod = "evening"

    weather = get_weather(city)
    weather_part = f"Current weather in {city}: {weather}." if weather else ""

    return f"Good {tod}, {name}! {weather_part} How can I help you today?"

def search_web(query):
    """Real-time web search using searchapi.io"""
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "q": query,
        "api_key": SEARCHAPI_API_KEY,
        "num": 5
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        # Check for API errors
        if data.get("error"):
            return f"Sorry, search API error: {data.get('error')}"
        
        if "answer_box" in data:
            answer = data["answer_box"].get("answer")
            if answer:
                return answer
        
        results = []
        if "organic_results" in data:
            for item in data["organic_results"][:3]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                results.append(f"• {title}: {snippet}")
        
        if results:
            return "\n".join(results)
        return None
    except Exception as e:
        return f"Sorry, search is not available right now. ({str(e)})"

def ask_openrouter(prompt, user_name="User"):
    """AI chat with personalized response using user's name"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": f"You are a helpful AI assistant named Sonic Bot, created by Arnicka Studios. You are talking to a user named {user_name}. Be friendly, helpful, and use their name occasionally in your responses."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=data)
        resp.raise_for_status()
        result = resp.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Sorry, I'm having trouble with AI right now. ({e})"

def is_search_query(text):
    """Check if the user is asking for current information"""
    search_keywords = [
        "search", "find", "what is", "who is", "when", "where", "how",
        "latest", "news", "current", "price", "stock", "weather", "define",
        "meaning", "what's", "who's", "compare", "best", "top"
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in search_keywords)

