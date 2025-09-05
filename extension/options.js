if (typeof window.browser === "undefined") window.browser = window.chrome;
const form = document.getElementById('options-form');
const targetLangSelect = document.getElementById('targetLang');
const sourceLangInput = document.getElementById('sourceLang');
const statusDiv = document.getElementById('status');

// Load saved language on page load
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const { targetLang, sourceLang } = await browser.storage.local.get(['targetLang', 'sourceLang']);
    if (targetLang) {
      targetLangSelect.value = targetLang;
    }
    if (sourceLang) {
      sourceLangInput.value = sourceLang;
    }
  } catch (e) {
    console.error("Error loading settings:", e);
  }
});

// Save language on form submit
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const targetLang = targetLangSelect.value;
  const sourceLang = sourceLangInput.value;
  
  try {
    const settings = { targetLang };
    // Only save sourceLang if it's not empty
    if (sourceLang) {
      settings.sourceLang = sourceLang;
    }
    await browser.storage.local.set(settings);
    statusDiv.textContent = 'Settings saved!';
    setTimeout(() => statusDiv.textContent = '', 2000);
  } catch (e) {
    statusDiv.textContent = 'Error saving settings.';
    console.error("Error saving settings:", e);
  }
});
