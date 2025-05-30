console.log("content.js loaded");
let currentPlatform = null;
let currentVideoId = null;
let video = null;
let settings = {};
let lastTime = 0;
previousTime = 0; // Reset when loading new video
let lastKnownDuration = 0;
let notifiedClaims = new Set();
let dingAudio = new Audio(chrome.runtime.getURL('sounds/ding.mp3'));
let lastDetectedVideoId = null;

const fakeClaims = [
  { time: 30, score: 0.2, text: "Minor error." },
  { time: 90, score: 0.6, text: "Significant false claim." },
  { time: 150, score: 0.9, text: "Major misinformation." }
];

async function sendToBackend(videoUrl) {
  console.log("Sending request to backend");
  try {
    const BASE_API = "http://localhost:5100";
        const response = await fetch(`${BASE_API}/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: videoUrl })
        });

        const result = await response.json();
        console.log("✅ Claims from backend:", result);

        // You can assign to fakeClaims here if result.gpt_analysis is properly formatted
        // fakeClaims = result.gpt_analysis.map(...);

    } catch (error) {
        console.error("❌ Error fetching claims:", error);
    }
}

function detectVideoPlatformAndId() {
  const url = new URL(window.location.href);

  if (url.hostname.includes("youtube.com")) {
    const id = new URLSearchParams(url.search).get("v");
    return { platform: "youtube", videoId: id };
  }

  if (url.hostname.includes("tiktok.com")) {
    const match = url.pathname.match(/\/video\/(\d+)/);
    if (match) {
      return { platform: "tiktok", videoId: match[1] };
    }

    // Try to extract from meta tag (for dynamically loaded pages like For You)
    const ogVideo = document.querySelector('meta[property="og:video:url"]');
    if (ogVideo) {
      const idMatch = ogVideo.content.match(/\/video\/(\d+)/);
      if (idMatch) {
        return { platform: "tiktok", videoId: idMatch[1] };
      }
    }
  }

  return { platform: null, videoId: null };
}

function observeTikTokVideoChanges() {
  const observer = new MutationObserver(() => {
    const currentUrl = window.location.href;
    const match = currentUrl.match(/\/video\/(\d+)/);
    const videoId = match ? match[1] : null;
    
    if (videoId && videoId !== lastDetectedVideoId) {
      console.log(`🔄 New TikTok video detected: ${videoId}`);
      lastDetectedVideoId = videoId;

      // Calling waveform redraw logic 
      setupWaveform();
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });
}

let lastPath = window.location.pathname;

/**
 * Special TikTok support logic: Detects when user navigates to a new video.
 * Handles removing the waveform on non-video TikTok pages (e.g., Explore).
 */
if (window.location.hostname.includes("tiktok.com")) {
  setInterval(() => {
    const currentPath = window.location.pathname;

    // ✅ Update lastPath only if path actually changed
    if (currentPath !== lastPath) {
      lastPath = currentPath;

      if (currentPath.startsWith("/explore")) {
        const waveform = document.getElementById("waveformContainer");
        if (waveform) {
          console.log("🧹 Removing waveform on TikTok Explore page.");
          waveform.remove();
        }
        console.log("🔕 On TikTok Explore, skipping plugin actions.");
        return;
      }

      if (!currentPath.includes("/video/") && document.getElementById("waveformContainer")) {
        console.log("🧹 Navigated away from video, removing waveform.");
        document.getElementById("waveformContainer").remove();
      }

      const match = currentPath.match(/\/video\/(\d+)/);
      if (match) {
        console.log("👀 TikTok path changed to new video:", match[1]);
        currentVideoId = match[1];
        waitForVideo();

        setTimeout(() => {
          video = document.querySelector("video");
          if (video) {
            console.log("🔄 Redrawing waveform for new TikTok video");
            // 🔁 First send to Whisper for analysis
            sendToBackend(window.location.href).then(() => {
              drawWaveform();
              startMarkerUpdate();
            });
          }
        }, 1000);
      }
    }
  }, 1000);
}

chrome.storage.sync.get([
  'bgColor', 'lineColor', 'timeMarkerColor', 'theme',
  'notificationDuration', 'jumpBackSeconds', 'showWaveform', 'soundEnabled'
], (data) => {
  settings = { ...data };
  waitForVideo();
});

/**
 * Listens for incoming messages from the settings popup.
 * Redraws the waveform with updated settings when the user saves new ones.
 */
chrome.runtime.onMessage.addListener((message) => {
  console.log("Message received:", message);
  console.log("New settings loaded, redrawing waveform...");
  if (message.action === "updateSettings") {
    chrome.storage.sync.get([
      'bgColor', 'lineColor', 'timeMarkerColor', 'theme',
      'notificationDuration', 'jumpBackSeconds', 'showWaveform', 'soundEnabled'
    ], (data) => {
      settings = {
        bgColor: data.bgColor,
        lineColor: data.lineColor,
        timeMarkerColor: data.timeMarkerColor,
        theme: data.theme,
        notificationDuration: data.notificationDuration,
        jumpBackSeconds: data.jumpBackSeconds,
        showWaveform: data.showWaveform,
        soundEnabled: data.soundEnabled
      };
	  console.log("New settings loaded, redrawing waveform...");
      applySettings();
    });
  }
});

function applyThemeSettings() {
  if (settings.theme === "light") {
    settings.bgColor = 'rgba(255,255,255,0.2)';
    settings.lineColor = '#1DB9FF';
    settings.timeMarkerColor = 'black';
  } else if (settings.theme === "dark") {
    settings.bgColor = 'rgba(0,0,0,0.3)';
    settings.lineColor = '#1DB9FF';
    settings.timeMarkerColor = 'white';
  }
  drawWaveform(); // redraw the bar immediately with new settings
}

/**
 * Repeatedly checks for the presence of a video element in the DOM.
 * Once found, initializes waveform and marker tracking.
 */
function waitForVideo() {
  const interval = setInterval(() => {
    video = document.querySelector('video');
    if (video) {
      clearInterval(interval);
      setupWaveform();
    }
  }, 500);
}


/**
 * Initializes the waveform container and inserts it into the page.
 * Called once a video element is detected and prepared for drawing.
 */
function setupWaveform() {
  const existing = document.getElementById('waveformContainer');
  if (existing) existing.remove();
  const container = document.createElement('div');
  container.id = 'waveformContainer';
  container.style.position = 'fixed';
  container.style.top = '15px'; // Lower the bar so it's visible
  container.style.left = '70%'; // Center better
  container.style.width = '20%'; // Wider
  container.style.height = '30px';
  container.style.zIndex = '5000';
  container.style.pointerEvents = 'none';
  container.style.backgroundColor = settings.bgColor || 'rgba(0,0,0,0.15)';
  container.style.borderRadius = '10px';
  container.style.display = settings.showWaveform ? 'block' : 'none';
  container.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
  document.body.appendChild(container);

  const marker = document.createElement('div');
  marker.id = 'timeMarker';
  marker.style.position = 'absolute';
  marker.style.top = '0';
  marker.style.width = '2px';
  marker.style.height = '100%';
  marker.style.backgroundColor = settings.timeMarkerColor || '#ffffff';
  container.appendChild(marker);

  drawWaveform();
  startMarkerUpdate();
}

function applySettings() {
  const container = document.getElementById('waveformContainer');
  if (container) {
    container.style.backgroundColor = settings.bgColor;
    container.style.display = settings.showWaveform ? 'block' : 'none';
  }
  const marker = document.getElementById('timeMarker');
  if (marker) {
    marker.style.backgroundColor = settings.timeMarkerColor;
  }
  drawWaveform();
}

/**
 * Draws the waveform visualization on the screen.
 * Uses global `fakeClaims` to plot data points on a horizontal timeline.
 * Creates and positions a canvas element with a line and dots that represent claims.
 */

function drawWaveform() {

  const container = document.getElementById('waveformContainer');
  if (!container) return;

  container.querySelectorAll('.claim-dot').forEach(dot => dot.remove());
  const oldCanvas = document.getElementById('waveformCanvas');
  if (oldCanvas) oldCanvas.remove();

  const canvas = document.createElement('canvas');
  canvas.id = 'waveformCanvas';
  canvas.width = container.offsetWidth;
  canvas.height = container.offsetHeight;
  canvas.style.position = 'absolute';
  canvas.style.top = '0';
  canvas.style.left = '0';
  container.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  ctx.strokeStyle = settings.lineColor || '#1DB9FF';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();

  const duration = video?.duration || lastKnownDuration || 200;

  fakeClaims.forEach(claim => {
    const x = (claim.time / duration) * canvas.width;

    const dot = document.createElement('div');
    dot.className = 'claim-dot';
    dot.style.position = 'absolute';
    dot.style.width = '8px';
    dot.style.height = '8px';
    dot.style.backgroundColor = getDotColor(claim.score);
    dot.style.borderRadius = '50%';
    dot.style.left = `${x - 4}px`;
    dot.style.top = `${(canvas.height / 2) - 4}px`;
    dot.style.zIndex = '1001';
    dot.style.pointerEvents = 'auto';
    dot.style.cursor = 'pointer';

    dot.addEventListener('mouseenter', (e) => {
      showTooltip(claim.text, e.pageX, e.pageY - 30);
    });

    dot.addEventListener('mouseleave', () => {
      hideTooltip();
    });

    dot.addEventListener('click', () => {
      let jumpTo = claim.time - (settings.jumpBackSeconds || 10);
      if (jumpTo < 0) jumpTo = 0;
      video.currentTime = jumpTo;
    });

    container.appendChild(dot);
  });
}

function getDotColor(score) {
  if (score <= 0.3) return 'gray';
  if (score <= 0.6) return 'yellow';
  if (score <= 0.8) return 'orange';
  return 'red';
}

/**
 * Starts an interval that updates the white time marker position as the video plays.
 * Also redraws the waveform if video duration changes.
 * Handles rewinding behavior and skipping over claims.
 */

function startMarkerUpdate() {
  const marker = document.getElementById('timeMarker');
  let lastKnownDuration = 0;
  let lastTime = 0;

  setInterval(() => {
    const currentVideo = document.querySelector("video");
    if (!currentVideo || !marker) return;

    video = currentVideo;

    const currentTime = video.currentTime;
    const duration = video.duration;

    // ✅ Skip glitchy time resets mid-video
    if (currentTime === 0 && lastTime > 2) return;

    const progress = (currentTime / duration) * 100;
    marker.style.left = `${progress}%`;

    // Rewind detection logic
    if (currentTime < lastTime) {
      for (let claim of fakeClaims) {
        if (claim.timestamp <= lastTime && claim.timestamp > currentTime) {
          notifiedClaims.delete(claim.timestamp);
        }
      }
    }

    lastTime = currentTime;

    checkForClaimNotification(currentTime);

    if (duration !== lastKnownDuration && duration > 0) {
      lastKnownDuration = duration;
      drawWaveform();
    }
  }, 100);
}

function showTooltip(text, x, y) {
  let tooltip = document.getElementById('floatingTooltip');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.id = 'floatingTooltip';
    tooltip.style.position = 'absolute';
    tooltip.style.padding = '5px 10px';
    tooltip.style.backgroundColor = 'black';
    tooltip.style.color = 'white';
    tooltip.style.borderRadius = '5px';
    tooltip.style.fontSize = '12px';
    tooltip.style.zIndex = '5002';
    tooltip.style.pointerEvents = 'none';
    document.body.appendChild(tooltip);
  }
  tooltip.textContent = text;
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${y}px`;
  tooltip.style.display = 'block';
}

function hideTooltip() {
  const tooltip = document.getElementById('floatingTooltip');
  if (tooltip) tooltip.style.display = 'none';
}
/**
 * Checks if a claim is currently reached based on the video time.
 * If a new claim timestamp is encountered, displays a popup and optionally plays a sound.
 *
 * @param {number} currentTime - The current timestamp of the video in seconds.
 */

function checkForClaimNotification(currentTime) {
  fakeClaims.forEach(claim => {
    if (!notifiedClaims.has(claim.time) && currentTime >= claim.time && currentTime - claim.time < 5) {
      showNotificationPopup(claim.text);
      notifiedClaims.add(claim.time);
    }
  });
}

function showNotificationPopup(text) {
  let popup = document.getElementById('claimNotificationPopup');
  if (!popup) {
    popup = document.createElement('div');
    popup.id = 'claimNotificationPopup';
    popup.style.position = 'fixed';
    popup.style.top = '70px';
    popup.style.right = '20px';
    popup.style.padding = '10px 20px';
    popup.style.backgroundColor = 'rgba(255,0,0,0.8)';
    popup.style.color = 'white';
    popup.style.borderRadius = '8px';
    popup.style.zIndex = '9999';
    popup.style.fontSize = '14px';
    popup.style.opacity = '0';
    popup.style.transition = 'opacity 0.5s ease';
    document.body.appendChild(popup);
  }
  popup.textContent = "Problematic Claim Detected: " + text;
  popup.style.opacity = '1';
  if (settings.soundEnabled) {
	dingAudio.play().catch(e => console.log('Ding sound failed:', e));
  }
  setTimeout(() => {
    popup.style.opacity = '0';
  }, (settings.notificationDuration || 15) * 1000);
    // ====== ADD DEBUG LOGS ======
  console.log("settings.soundEnabled =", settings.soundEnabled);
  if (dingAudio) {
    console.log("dingAudio object exists");
    if (settings.soundEnabled) {
      console.log("Trying to play ding sound...");
      dingAudio.play().then(() => {
        console.log("Ding sound played successfully");
      }).catch((e) => {
        console.error("Ding play blocked/error:", e);
      });
    } else {
      console.log("Sound is disabled in settings, not playing ding.");
    }
  } else {
    console.error("dingAudio is undefined ");
  }
}
// ====== END DEBUG LOGS ======
/**
 * YouTube-specific behavior: Watches for new videos and triggers redraw accordingly.
 */
if (window.location.hostname.includes("youtube.com")) {
  let lastVideoId = "";

  setInterval(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const currentVideoId = urlParams.get("v");

    if (currentVideoId && currentVideoId !== lastVideoId) {
      lastVideoId = currentVideoId;
      console.log("🔄 YouTube video changed:", currentVideoId);

      waitForVideo();
      setTimeout(() => {
        video = document.querySelector("video");
        if (video) {
          console.log("🔄 Redrawing waveform for new YouTube video");
          sendToBackend(window.location.href).then(() => {
            drawWaveform();
            startMarkerUpdate();
          });
        }
      }, 1000);
    }
  }, 1000);
}