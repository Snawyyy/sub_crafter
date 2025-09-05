if (typeof window.browser === "undefined") window.browser = window.chrome;
const statusDiv = document.getElementById('status');
const startButton = document.getElementById('start-button');
const targetLangSelect = document.getElementById('targetLang');
const sourceLangInput = document.getElementById('sourceLang');
const hardcodeCheckbox = document.getElementById('hardcode');

let ws;

// Load saved language and set the dropdown
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const { targetLang, sourceLang, hardcode } = await browser.storage.local.get(['targetLang', 'sourceLang', 'hardcode']);
    if (targetLang) {
      targetLangSelect.value = targetLang;
    }
    if (sourceLang) {
      sourceLangInput.value = sourceLang;
    }
    // Checkbox is checked by default, only uncheck if explicitly saved as false
    if (hardcode === false) {
      hardcodeCheckbox.checked = false;
    }
  } catch (e) {
    console.error("Error loading settings:", e);
  }
});

// Save language preference when it changes
targetLangSelect.addEventListener('change', async (e) => {
  try {
    await browser.storage.local.set({ targetLang: e.target.value });
  } catch (e) {
    console.error("Error saving settings:", e);
  }
});

// Save source language when it changes
sourceLangInput.addEventListener('change', async (e) => {
  try {
    await browser.storage.local.set({ sourceLang: e.target.value });
  } catch (e) {
    console.error("Error saving settings:", e);
  }
});

// Save hardcode preference when it changes
hardcodeCheckbox.addEventListener('change', async (e) => {
  try {
    await browser.storage.local.set({ hardcode: e.target.checked });
  } catch (e) {
    console.error("Error saving settings:", e);
  }
});

startButton.addEventListener('click', async () => {
  try {
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });

    if (!tab.url || !tab.url.includes("youtube.com/watch")) {
      statusDiv.textContent = "Not a YouTube video page.";
      return;
    }

    const targetLang = targetLangSelect.value || "he";
    const sourceLang = sourceLangInput.value || null; // null will trigger auto-detection
    const hardcode = hardcodeCheckbox.checked;

    statusDiv.textContent = 'Sending to backend...';
    
    // Prepare the request payload
    const payload = { 
      url: tab.url,
      target_lang: targetLang,
      hardcode: hardcode
    };
    
    // Only add source_lang if it's specified
    if (sourceLang) {
      payload.source_lang = sourceLang;
    }
    
    const response = await fetch("http://localhost:8000/enqueue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    const { job_id } = data;

    statusDiv.textContent = `Job queued (ID: ${job_id.substring(0, 6)}...)`;
    connectToWebSocket(job_id);

  } catch (error) {
    statusDiv.textContent = 'Error: Could not connect to backend.';
    console.error("Error:", error);
  }
});

function connectToWebSocket(job_id) {
  if (ws) {
    ws.close();
  }

  ws = new WebSocket(`ws://localhost:8000/ws/${job_id}`);

  ws.onopen = () => {
    console.log(`WebSocket connected for job ${job_id}`);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    statusDiv.textContent = `Status: ${data.status}`;
  };

  ws.onerror = (error) => {
    statusDiv.textContent = 'WebSocket error.';
    console.error('WebSocket Error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected.');
  };
}
