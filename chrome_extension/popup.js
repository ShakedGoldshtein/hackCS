document.getElementById("analyze-btn").addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url) {
        document.getElementById("result").innerText = "לא הצלחנו לקרוא את כתובת הסרטון.";
        return;
    }

    const videoUrl = tab.url;

    // בדיקה שהכתובת היא של סרטון טיקטוק
    if (!videoUrl.includes("tiktok.com") || !videoUrl.includes("/video/")) {
        document.getElementById("result").innerText = "אנא פתח סרטון טיקטוק לפני הלחיצה על הכפתור.";
        return;
    }

    // הצגת הודעה זמנית
    document.getElementById("result").innerText = "⏳ מנתח את הסרטון...";

    try {
        const response = await fetch("https://2d0f-132-69-234-140.ngrok-free.app/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: videoUrl })
        });

        const contentType = response.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
            const text = await response.text();
            document.getElementById("result").innerText =
                "❌ שגיאה מהשרת:\n\n" + text;
            return;
        }

        const result = await response.json();
        document.getElementById("result").innerText =
            "✅ " + result.verdict + "\n\n" +
            result.reason + "\n\n" +
            "🔎 ניתוח GPT:\n" + result.gpt_analysis;

    } catch (error) {
        document.getElementById("result").innerText = "❌ שגיאה: " + error.message;
    }
});