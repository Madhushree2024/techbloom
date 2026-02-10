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

    online[visitor_id] = now
    data["online"] = online
    save_data(data)

    # Get category from URL
    category = request.args.get("category", "").strip()
    category_lower = category.lower()

    # Fetch news from Hacker News
    url = "https://hn.algolia.com/api/v1/search_by_date?tags=story"
    all_articles = requests.get(url).json()["hits"]

    # Filter articles by category keyword in title
    filtered_articles = [
        a for a in all_articles
        if category_lower in (a.get("title") or "").lower()
    ] if category_lower else all_articles

    # Ensure at least 6 articles, fill with other trending stories if needed
    articles = filtered_articles[:6]
    if len(articles) < 6:
        remaining = [a for a in all_articles if a not in articles]
        articles += remaining[:6 - len(articles)]

    resp = make_response(render_template(
        "home.html",
        articles=articles,
        visitors=data["total"],
        online=len(online),
        category=category if category else "Tech"
    ))
    resp.set_cookie("visitor_id", visitor_id, max_age=60*60*24*365)
    return resp


if __name__ == "__main__":
    app.run(debug=True)
