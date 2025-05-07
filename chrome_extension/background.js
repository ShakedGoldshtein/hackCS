// background.js

chrome.runtime.onInstalled.addListener(() => {
  console.log("✅ background.js installed and running.");
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log("📨 Message received in background:", message);

  if (message.type === "ping") {
    sendResponse({ reply: "pong from background" });
  }

  return true;
});