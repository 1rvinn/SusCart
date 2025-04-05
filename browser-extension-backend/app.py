from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from rapidfuzz import fuzz

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

BASE_URL = "https://refitglobal.com"

def is_relevant(query, title):
    """Returns True if the title is a close match to the query"""
    similarity = fuzz.partial_ratio(query.lower(), title.lower())
    return similarity > 60  # Adjust this threshold as needed

@app.route("/search", methods=["GET"])
def search_products():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "No search query provided"}), 400

    search_url = f"{BASE_URL}/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        print("🔍 Searching on ReFitGlobal:", search_url)
        response = requests.get(search_url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Failed to fetch data. Status code: {response.status_code}")
            return jsonify({"error": "Failed to fetch data from ReFit"}), 500

        soup = BeautifulSoup(response.text, "lxml")
        product_cards = soup.find_all("div", class_='card__content')
        print(f"🧾 Found {len(product_cards)} product cards")

        product_list = []
        seen_titles = set()

        for i, card in enumerate(product_cards):
            try:
                link_tag = card.select_one("a.full-unstyled-link")
                title_tag = card.select_one("h3.card__heading")
                price_tag = card.select_one("span.price-item--regular")
                image_tag = card.select_one("img")

                if not all([link_tag, title_tag, price_tag, image_tag]):
                    print(f"⚠️ Skipping card {i} due to missing elements")
                    continue

                title = title_tag.get_text(strip=True)
                price = price_tag.get_text(strip=True)
                image_url = urljoin(BASE_URL, image_tag["src"])

                raw_link = link_tag["href"]
                clean_link = raw_link.split("?")[0]
                link = urljoin(BASE_URL, clean_link)

                print(f"✅ Card {i}: {title} | {price}")

                if title not in seen_titles and is_relevant(query, title):
                    seen_titles.add(title)
                    product_list.append({
                        "title": title,
                        "price": price,
                        "link": link,
                        "image": image_url
                    })

            except Exception as inner_e:
                print(f"💥 Error processing card {i}:", inner_e)

        return jsonify(product_list)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("🚀 Starting Flask server on http://localhost:5001")
    app.run(port=5001, debug=True)
