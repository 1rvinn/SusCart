console.log("🔍 Content script loaded");

function detectProductSearch() {
    let url = window.location.href;
    let productName = "";

    if (url.includes("amazon.in")) {
        let titleElement = document.getElementById("productTitle");
        if (titleElement) productName = titleElement.textContent.trim();
    }

    if (url.includes("flipkart.com")) {
        let titleElement = document.querySelector(".VU-ZEz");
        if (titleElement) productName = titleElement.textContent.trim();
    }

    if (productName) {
        console.log("🔎 Detected Product:", productName);

        // 🧼 Clean product name before sending to Flask
        const cleanedName = productName
            .replace(/\(.*?\)/g, "")   // remove anything in brackets like (512GB)
            .replace(/-\s.*$/, "")     // remove dash and anything after (- Starlight)
            .replace(/\s+/g, " ")      // remove extra spaces
            .trim();

        console.log("🧼 Cleaned Product Name:", cleanedName);

        fetchSecondHandProducts(cleanedName);
    }
}

function fetchSecondHandProducts(productName) {
    console.log("🛒 Searching second-hand options for:", productName);

    fetch(`http://127.0.0.1:5001/search?query=${encodeURIComponent(productName)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("❌ Error fetching products:", data.error);
                return;
            }

            console.log("✅ Received Second-Hand Products:", data);
            console.log("🔢 Number of products received:", data.length);
            displayProducts(data);
        })
        .catch(error => console.error("❌ Failed to fetch products:", error));
}

function displayProducts(products) {
    let container = document.createElement("div");
    container.style.position = "fixed";
    container.style.top = "10px";
    container.style.right = "10px";
    container.style.width = "300px";
    container.style.backgroundColor = "white";
    container.style.border = "1px solid #ccc";
    container.style.padding = "10px";
    container.style.zIndex = "1000";
    container.style.boxShadow = "2px 2px 10px rgba(0,0,0,0.2)";

    let title = document.createElement("h3");
    title.innerText = "♻️ Eco - Friendly Alternatives";
    container.appendChild(title);

    products.forEach(product => {
        let productElement = document.createElement("div");
        productElement.innerHTML = `
            <p><strong>${product.title}</strong></p>
            <p>Price: ${product.price}</p>
            <a href="${product.link}" target="_blank">🔗 View</a>
            <hr>
        `;
        container.appendChild(productElement);
    });

    document.body.appendChild(container);
}

detectProductSearch();
