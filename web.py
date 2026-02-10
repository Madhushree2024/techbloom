from flask import Flask, render_template, request, make_response
import requests
import json
import os
import time

app = Flask(__name__)

COUNT_FILE = "visitors.json"
ONLINE_WINDOW = 30  # seconds

NEWS_API_KEY = "ndh_wodNG5JPFNl0UZeCmV2V1CNcf9RMFEiERt_A2S1cth0"
NEWS_API_URL = "https://api.newsdatahub.com/v1/news"

def load_data():
    if not os.path.exists(COUNT_FILE):
        return {"total": 0, "online": {}}
    with open(COUNT_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(COUNT_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def home():
    data = load_data()
    online = data["online"]
    now = time.time()

    online = {k: v for k, v in online.items() if now - v < ONLINE_WINDOW}
    visitor_id = request.cookies.get("visitor_id")
    if not visitor_id:
        visitor_id = str(now) + request.remote_addr
        data["total"] += 1

    online[visitor_id] = now
    data["online"] = online
    save_data(data)

    category = request.args.get("category", "").strip()
    category_param = category if category else "technology"

    # NewsDataHub request
    headers = {
        "X-API-Key": NEWS_API_KEY,
        "User-Agent": "TechBloomNewsApp/1.0"
    }
    params = {
        "topic": category_param.lower(),  # filter by topic
        "language": "en",
        "per_page": 6
    }

    response = requests.get(NEWS_API_URL, headers=headers, params=params)
    news_data = response.json().get("data", [])

    # Fallback to empty list if no articles
    articles = news_data if isinstance(news_data, list) else []

    resp = make_response(render_template(
        "home.html",
        articles=articles,
        visitors=data["total"],
        online=len(online),
        category=category_param
    ))
    resp.set_cookie("visitor_id", visitor_id, max_age=60*60*24*365)
    return resp

if __name__ == "__main__":
    app.run(debug=True)
