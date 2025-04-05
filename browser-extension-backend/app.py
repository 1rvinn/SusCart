from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from rapidfuzz import fuzz
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# OpenRouter API Key
OPENROUTER_API_KEY = "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"
MODEL_ID = "mistralai/mistral-small-3.1-24b-instruct:free"

# ----------- Query Refinement using OpenRouter (Mistral) ----------- #
def refine_query_with_mistral(product_title):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5001",
        "X-Title": "EcoSearchApp",
    }

    prompt = f"Extract only the general product type from this product title: '{product_title}'. Keep it short (1-3 words), lowercase, no brand or color."

    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()
        print("🪵 Mistral raw response:", result)

        if "choices" not in result:
            raise ValueError("Mistral API did not return 'choices': " + str(result))

        content = result["choices"][0]["message"]["content"]
        return content.strip().lower()
    except Exception as e:
        print("❌ Mistral API error:", e)
        return product_title

def is_relevant(query, title):
    return fuzz.partial_ratio(query.lower(), title.lower()) > 60

# ------------------- ReFitGlobal Scraper ------------------- #
def fetch_refit(query):
    BASE_URL = "https://refitglobal.com"
    search_url = f"{BASE_URL}/search?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")
        cards = soup.find_all("div", class_='card__content')

        results, seen = [], set()
        for i, card in enumerate(cards):
            if len(results) >= 2: break
            try:
                title = card.select_one("h3.card__heading").get_text(strip=True)
                price = card.select_one("span.price-item--regular").get_text(strip=True)
                link = urljoin(BASE_URL, card.select_one("a.full-unstyled-link")["href"].split("?")[0])
                image = urljoin(BASE_URL, card.select_one("img")["src"])

                if title in seen or not is_relevant(query, title): continue
                seen.add(title)

                results.append({
                    "site": "ReFitGlobal",
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": image
                })
            except Exception as e:
                print(f"⚠️ Error parsing ReFit card {i}:", e)
        return results
    except Exception as e:
        print("❌ Error fetching from ReFit:", e)
        return []

# ------------------- GreenFeels Scraper ------------------- #
def fetch_greenfeels(query):
    BASE_URL = "https://greenfeels.in"
    search_url = f"{BASE_URL}/search?q={query}&options%5Bprefix%5D=last&type=product"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.find_all("li", class_="product")

        results = []
        for i, product in enumerate(products):
            if len(results) >= 2: break
            try:
                data = product.find("div", class_="product-item").get("data-json-product")
                if not data:
                    continue
                product_data = json.loads(data)
                name = product_data.get("name", "Unnamed")
                handle = product_data.get("handle", "")
                price = product_data.get("variants", [{}])[0].get("price", "0")

                results.append({
                    "site": "GreenFeels",
                    "title": name,
                    "price": f"₹{price}",
                    "link": f"{BASE_URL}/products/{handle}",
                    "image": None
                })
            except Exception as e:
                print(f"⚠️ Error parsing GreenFeels product {i}:", e)
        return results
    except Exception as e:
        print("❌ Error fetching from GreenFeels:", e)
        return []

# ------------------- BrownLiving Scraper ------------------- #
def fetch_brownliving(query):
    BASE_URL = "https://brownliving.in"
    search_url = f"{BASE_URL}/search?options%5Bprefix%5D=last&q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        product_containers = soup.find_all("div", class_="product-card__content")

        results = []
        for i, container in enumerate(product_containers):
            if len(results) >= 2: break
            try:
                title_tag = container.select_one("a.product-card__title")
                price_tag = container.select_one("span.money")
                if not (title_tag and price_tag): continue

                title = title_tag.get_text(strip=True)
                price = price_tag.get_text(strip=True)
                link = urljoin(BASE_URL, title_tag.get("href"))

                results.append({
                    "site": "BrownLiving",
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": None
                })
            except Exception as e:
                print(f"⚠️ Error parsing BrownLiving product {i}:", e)
        return results
    except Exception as e:
        print("❌ Error fetching from BrownLiving:", e)
        return []

# ------------------- Flask Endpoint ------------------- #
@app.route("/search", methods=["GET"])
def search_products():
    original_query = request.args.get("query", "").strip()
    if not original_query:
        return jsonify({"error": "No search query provided"}), 400

    print(f"🔍 Original query: {original_query}")
    refined_query = refine_query_with_mistral(original_query)
    print(f"🧠 Refined query: {refined_query}")

    results = []
    results += fetch_refit(refined_query)
    results += fetch_greenfeels(refined_query)
    results += fetch_brownliving(refined_query)

    return jsonify(results)

@app.route("/healthcheck")
def healthcheck():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("🚀 Starting Flask server on http://localhost:5001")
    app.run(debug=True, port=5001)
