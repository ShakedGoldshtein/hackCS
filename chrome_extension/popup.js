const defaultSettings = {
    bgColor: 'rgba(0, 0, 0, 0.3)',
    lineColor: '#1DB9FF',
    timeMarkerColor: '#ffffff',
    notificationDuration: 15,
    jumpBackSeconds: 10,
    showWaveform: true,
    soundEnabled: true
};

const PARENT_PASSWORD = 'admin123';  // ← your chosen secret

document.addEventListener('DOMContentLoaded', () => {
  const passInput = document.getElementById('parentPassword');
  const btn       = document.getElementById('parentModeBtn');

  // Initialize button text based on saved state
  chrome.storage.sync.get('parentMode', ({ parentMode }) => {
    btn.textContent = parentMode
      ? 'Deactivate Parent Mode'
      : 'Activate Parent Mode';
  });

  btn.addEventListener('click', () => {
    const entered = passInput.value;
    if (entered !== PARENT_PASSWORD) {
      alert('Incorrect password.');
      return;
    }

    // Toggle the stored value
    chrome.storage.sync.get('parentMode', ({ parentMode }) => {
      const newVal = !parentMode;
      chrome.storage.sync.set({ parentMode: newVal }, () => {
        btn.textContent = newVal
          ? 'Deactivate Parent Mode'
          : 'Activate Parent Mode';
        passInput.value = '';  // clear after use
      });
    });
  });
});

document.addEventListener('DOMContentLoaded', loadSettings);
document.getElementById('saveSettings').addEventListener('click', () => {
    const bgColorHex = document.getElementById('bgColor').value;
    const bgAlpha = parseFloat(document.getElementById('bgAlpha').value);
    const lineColor = document.getElementById('lineColor').value;
    const timeMarkerColor = document.getElementById('timeMarkerColor').value;
    const notificationDuration = parseInt(document.getElementById('notificationDuration').value) || 15;
    const jumpBackSeconds = parseInt(document.getElementById('jumpBackSeconds').value) || 10;
    const showWaveform = document.getElementById('showWaveform').checked;
    const soundEnabled = document.getElementById('soundEnabled').checked;

    const bgColorRGBA = hexToRGBA(bgColorHex, bgAlpha);

    chrome.storage.sync.set({
        bgColor: bgColorRGBA,
        lineColor,
        timeMarkerColor,
        notificationDuration,
        jumpBackSeconds,
        showWaveform,
        soundEnabled
    }, () => {
        // send message properly to active tab
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length > 0) {
                chrome.tabs.sendMessage(tabs[0].id, { action: "updateSettings" }).catch((error) => {
                    console.warn("Could not send message:", error);
                });
            }
        });
    });
});

document.getElementById('resetSettings').addEventListener('click', () => {
    chrome.storage.sync.set(defaultSettings, () => {
        // After saving defaults, send update to the active tab
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length > 0) {
                chrome.tabs.sendMessage(tabs[0].id, { action: "updateSettings" }).catch((error) => {
                    console.warn("Could not send message after restoring defaults:", error);
                });
            }
        });

        loadSettings(); // Reloads the popup UI values visually
    });
});

function loadSettings() {
    chrome.storage.sync.get(Object.keys(defaultSettings), (data) => {
        document.getElementById('bgColor').value = rgbaToHex(data.bgColor || defaultSettings.bgColor);
        document.getElementById('bgAlpha').value = rgbaToAlpha(data.bgColor || defaultSettings.bgColor);
        document.getElementById('lineColor').value = data.lineColor || defaultSettings.lineColor;
        document.getElementById('timeMarkerColor').value = data.timeMarkerColor || defaultSettings.timeMarkerColor;
        document.getElementById('notificationDuration').value = data.notificationDuration || defaultSettings.notificationDuration;
        document.getElementById('jumpBackSeconds').value = data.jumpBackSeconds || defaultSettings.jumpBackSeconds;
        document.getElementById('showWaveform').checked = data.showWaveform !== false;
        document.getElementById('soundEnabled').checked = data.soundEnabled !== false;
    });
}

function hexToRGBA(hex, alpha) {
    const r = parseInt(hex.substr(1, 2), 16);
    const g = parseInt(hex.substr(3, 2), 16);
    const b = parseInt(hex.substr(5, 2), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function rgbaToHex(rgba) {
    if (!rgba) return '#000000';
    const parts = rgba.match(/\d+/g);
    if (!parts) return '#000000';
    const r = parseInt(parts[0]).toString(16).padStart(2, '0');
    const g = parseInt(parts[1]).toString(16).padStart(2, '0');
    const b = parseInt(parts[2]).toString(16).padStart(2, '0');
    return `#${r}${g}${b}`;
}

function rgbaToAlpha(rgba) {
    if (!rgba) return 0.3;
    const parts = rgba.match(/[\d\.]+/g);
    if (!parts || parts.length < 4) return 0.3;
    return parseFloat(parts[3]);
}
