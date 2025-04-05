import requests
from bs4 import BeautifulSoup
import json

query = "iPhone"
url = f"https://refitglobal.com/search?q={query}"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "lxml")
    products = soup.find_all("div", class_='card__content')

    product_list = []
    seen_titles = set()

    if products:
        for product in products:
            title_element = product.find("h3")
            price_element = product.find("span", class_="price-item price-item--regular")  
            link_element = product.find("a")

            title = title_element.text.strip() if title_element else None
            price = price_element.get_text(strip=True) if price_element else None
            link = "https://refitglobal.com" + link_element["href"] if link_element else None

            # ✅ Ensure price is not None and contains ₹
            if price and "₹" not in price:
                price = "₹" + price  

            # Debugging: Print extracted values
            print(f"Title: {title}, Price: {price}, Link: {link}")

            # Ensure valid title, valid price (ignore 'None'), and avoid duplicates
            if title and price and title not in seen_titles:
                seen_titles.add(title)
                product_list.append({"title": title, "price": price, "link": link})

    # Save as JSON with UTF-8 Encoding
    if product_list:
        with open("refit_products.json", "w", encoding="utf-8") as f:
            json.dump(product_list, f, indent=4, ensure_ascii=False)
        print("✅ Data saved to refit_products.json")
    else:
        print("⚠️ No valid products found. Check if the website structure changed.")

else:
    print("❌ Failed to fetch data from ReFit.")
