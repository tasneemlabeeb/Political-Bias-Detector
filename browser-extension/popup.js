/**
 * Popup Script
 *
 * Handles the extension popup UI and communicates with the content script.
 */

const BIAS_COLORS = {
  'Left-Leaning': '#1565C0',
  'Center-Left': '#42A5F5',
  'Centrist': '#78909C',
  'Center-Right': '#EF5350',
  'Right-Leaning': '#C62828',
};

const statusEl = document.getElementById('status');
const loadingEl = document.getElementById('loading');
const resultEl = document.getElementById('result');
const analyzeBtn = document.getElementById('analyzeBtn');
const settingsBtn = document.getElementById('settingsBtn');
const settingsPanel = document.getElementById('settingsPanel');
const apiUrlInput = document.getElementById('apiUrlInput');
const autoAnalyzeToggle = document.getElementById('autoAnalyzeToggle');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');

// Analyze current page
analyzeBtn.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  statusEl.style.display = 'none';
  loadingEl.classList.add('active');
  resultEl.style.display = 'none';

  chrome.tabs.sendMessage(tab.id, { action: 'analyze' }, (response) => {
    if (chrome.runtime.lastError) {
      showError('Cannot analyze this page. Navigate to a news article and try again.');
      return;
    }
    // Poll for results
    setTimeout(() => checkForResults(tab), 2500);
  });
});

async function checkForResults(tab) {
  chrome.tabs.sendMessage(tab.id, { action: 'getLastAnalysis' }, (response) => {
    if (chrome.runtime.lastError || !response) {
      showError('Analysis failed. Make sure your backend is running.');
      return;
    }
    if (response.url === tab.url && response.result) {
      showResults(response.result);
    } else {
      showError('No results yet. The page may not contain a detectable article.');
    }
  });
}

function showResults(result) {
  loadingEl.classList.remove('active');
  statusEl.style.display = 'none';
  resultEl.style.display = 'block';

  const bias = result.bias || 'Centrist';
  const color = BIAS_COLORS[bias] || '#78909C';
  const confidence = Math.round((result.confidence || 0) * 100);
  const spectrumLeft = Math.round((result.spectrum_left || 0.33) * 100);
  const spectrumCenter = Math.round((result.spectrum_center || 0.34) * 100);
  const spectrumRight = Math.round((result.spectrum_right || 0.33) * 100);
  const intensity = Math.round((result.bias_intensity || 0) * 100);

  resultEl.innerHTML = `
    <div class="result-label" style="background: ${color};">
      ${bias}
    </div>
    <div class="result-details">
      <div class="detail-row">
        <span>Confidence:</span>
        <span>${confidence}%</span>
      </div>
      <div class="detail-row">
        <span>Bias Intensity:</span>
        <span>${intensity}%</span>
      </div>
      <div class="detail-row">
        <span>Left Leaning:</span>
        <span>${spectrumLeft}%</span>
      </div>
      <div class="detail-row">
        <span>Center:</span>
        <span>${spectrumCenter}%</span>
      </div>
      <div class="detail-row">
        <span>Right Leaning:</span>
        <span>${spectrumRight}%</span>
      </div>
      <div class="detail-row">
        <span>Model:</span>
        <span>${result.model_used || 'ml'}</span>
      </div>
      ${result.reasoning ? `<div class="detail-row" style="flex-direction:column;gap:4px;"><span>Reasoning:</span><span style="font-size:12px;line-height:1.4;">${result.reasoning}</span></div>` : ''}
    </div>
  `;
}

function showError(message) {
  loadingEl.classList.remove('active');
  statusEl.style.display = 'block';
  resultEl.style.display = 'none';
  statusEl.innerHTML = `
    <div class="status-icon">&#9888;&#65039;</div>
    <div class="status-text">${message}</div>
  `;
}

// Settings toggle
settingsBtn.addEventListener('click', () => {
  const isVisible = settingsPanel.style.display === 'block';
  settingsPanel.style.display = isVisible ? 'none' : 'block';
});

// Load saved settings
chrome.storage.sync.get(['apiUrl', 'autoAnalyze'], (data) => {
  apiUrlInput.value = data.apiUrl || 'http://localhost:8000/api/v1';
  autoAnalyzeToggle.checked = data.autoAnalyze !== false;
});

// Save settings
saveSettingsBtn.addEventListener('click', () => {
  chrome.storage.sync.set({
    apiUrl: apiUrlInput.value.replace(/\/+$/, ''),
    autoAnalyze: autoAnalyzeToggle.checked,
  }, () => {
    saveSettingsBtn.textContent = 'Saved!';
    setTimeout(() => { saveSettingsBtn.textContent = 'Save'; }, 1500);
  });
});

// Load last analysis on popup open
window.addEventListener('DOMContentLoaded', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.tabs.sendMessage(tab.id, { action: 'getLastAnalysis' }, (response) => {
    if (chrome.runtime.lastError) return;
    if (response && response.url === tab.url && response.result) {
      showResults(response.result);
    }
  });
});
