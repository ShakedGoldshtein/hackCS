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
        const response = await fetch("https://0c5a-132-69-234-130.ngrok-free.app/analyze", {
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
        // וידוא שמבנה הנתונים תקין
        if (!result.gpt_analysis || !Array.isArray(result.gpt_analysis)) {
            document.getElementById("result").innerText = "❌ שגיאה: פורמט תשובת השרת אינו תקין.";
            return;
        }
        document.getElementById("result").innerText =
            "טענות שזוהו בטקסט:\n\n" +
            result.gpt_analysis.map((entry, i) =>
                `טענה מספר ${i + 1}:\n"${entry.claim}"\n\n` +
                `${entry.verdict === "true" ? "אמין" : (entry.verdict === "false" ? "לא אמין" : "❓ לא ידוע")}\n` +
                `${entry.gpt_answer ? "נימוק: " + entry.gpt_answer : "ℹ️ לא סופק נימוק"}\n`
            ).join("\n\n");

    } catch (error) {
        document.getElementById("result").innerText = "❌ שגיאה: " + error.message;
    }
});