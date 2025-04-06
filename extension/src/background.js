console.log("✅ Background script loaded...");

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "fetchSecondHandOptions") {
        console.log(`🔍 Fetching second-hand options for: ${request.productTitle}`);

        // Fetch data from your Flask backend
        fetch(`http://127.0.0.1:5001/search?query=${encodeURIComponent(request.productTitle)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error("❌ Error fetching data:", data.error);
                    sendResponse({ success: false, error: data.error });
                } else {
                    console.log("✅ Received second-hand options:", data);
                    sendResponse({ success: true, data: data });
                }
            })
            .catch(error => {
                console.error("❌ Fetch error:", error);
                sendResponse({ success: false, error: error.toString() });
            });

        return true; // Keep the message channel open for asynchronous response
    }
});
