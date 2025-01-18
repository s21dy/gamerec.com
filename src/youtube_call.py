import requests 
import json

API_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_BASE = "https://www.youtube.com/watch?"
api_key = ""

with open("../.env/config.json") as config_file:
    config = json.load(config_file)
    api_key = config["YOUTUBE_API_KEY"]

def fetch_youtube_data(game_name):
    try:
        params = {"part": "snippet", 
                  "q": game_name + " game lets play",
                  "type": "video","key": api_key,
                  "maxResults":5 }
        response = requests.get(API_URL, params=params).json()
        data = response[""]
        return data[0]['id']['videoId']
    except Exception as e:
        return f"Error: {e}"
