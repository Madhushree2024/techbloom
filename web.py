from flask import Flask, render_template, request, make_response
import requests
import json
import os
import time

app = Flask(__name__)

COUNT_FILE = "visitors.json"
ONLINE_WINDOW = 30  # seconds


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

    # Clean old online users
    online = {k: v for k, v in online.items() if now - v < ONLINE_WINDOW}

    visitor_id = request.cookies.get("visitor_id")

    if not visitor_id:
        visitor_id = str(now) + request.remote_addr
        data["total"] += 1

    # Update online
    online[visitor_id] = now

    data["online"] = online
    save_data(data)

    # Fetch news
    url = "https://hn.algolia.com/api/v1/search_by_date?tags=story"
    articles = requests.get(url).json()["hits"][:6]

    resp = make_response(render_template(
        "home.html",
        articles=articles,
        visitors=data["total"],
        online=len(online)
    ))
    resp.set_cookie("visitor_id", visitor_id, max_age=60*60*24*365)

    return resp


if __name__ == "__main__":
    app.run(debug=True)
