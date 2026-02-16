/**
 * Popup Script
 * 
 * Handles popup UI interactions.
 */

const biasColors = {
  'Left-Leaning': '#1565C0',
  'Center-Left': '#42A5F5',
  'Centrist': '#78909C',
  'Center-Right': '#EF5350',
  'Right-Leaning': '#C62828',
};

// Elements
const statusEl = document.getElementById('status');
const loadingEl = document.getElementById('loading');
const resultEl = document.getElementById('result');
const analyzeBtn = document.getElementById('analyzeBtn');
const optionsBtn = document.getElementById('optionsBtn');

// Analyze current page
analyzeBtn.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  // Show loading
  statusEl.style.display = 'none';
  loadingEl.classList.add('active');
  resultEl.style.display = 'none';
  
  // Send message to content script
  chrome.tabs.sendMessage(
    tab.id,
    { action: 'analyze' },
    (response) => {
      if (chrome.runtime.lastError) {
        console.error(chrome.runtime.lastError);
        showError('Failed to analyze page. Make sure you\'re on a news article.');
        return;
      }
      
      // Wait for analysis to complete
      setTimeout(checkForResults, 2000);
    }
  );
});

// Check for analysis results
async function checkForResults() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  chrome.tabs.sendMessage(
    tab.id,
    { action: 'getLastAnalysis' },
    (response) => {
      if (chrome.runtime.lastError) {
        showError('Failed to get results');
        return;
      }
      
      if (response && response.url === tab.url) {
        showResults(response.result);
      } else {
        showError('No analysis available for this page');
      }
    }
  );
}

// Show results in popup
function showResults(result) {
  loadingEl.classList.remove('active');
  statusEl.style.display = 'none';
  resultEl.style.display = 'block';
  
  const color = biasColors[result.bias_label] || '#78909C';
  const confidence = Math.round(result.confidence * 100);
  
  resultEl.innerHTML = `
    <div class="result-label" style="background: ${color};">
      ${result.bias_label}
    </div>
    <div class="result-details">
      <div class="detail-row">
        <span>Confidence:</span>
        <span>${confidence}%</span>
      </div>
      <div class="detail-row">
        <span>Direction Score:</span>
        <span>${result.direction_score.toFixed(2)}</span>
      </div>
      <div class="detail-row">
        <span>Bias Intensity:</span>
        <span>${Math.round(result.intensity_score * 100)}%</span>
      </div>
      <div class="detail-row">
        <span>Left Leaning:</span>
        <span>${Math.round(result.spectrum.left * 100)}%</span>
      </div>
      <div class="detail-row">
        <span>Center:</span>
        <span>${Math.round(result.spectrum.center * 100)}%</span>
      </div>
      <div class="detail-row">
        <span>Right Leaning:</span>
        <span>${Math.round(result.spectrum.right * 100)}%</span>
      </div>
    </div>
  `;
}

// Show error message
function showError(message) {
  loadingEl.classList.remove('active');
  statusEl.style.display = 'block';
  resultEl.style.display = 'none';
  
  statusEl.innerHTML = `
    <div class="status-icon">⚠️</div>
    <div class="status-text">${message}</div>
  `;
}

// Options button
optionsBtn.addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
});

// Load last analysis on popup open
window.addEventListener('DOMContentLoaded', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  chrome.tabs.sendMessage(
    tab.id,
    { action: 'getLastAnalysis' },
    (response) => {
      if (chrome.runtime.lastError) {
        // Content script not loaded yet
        return;
      }
      
      if (response && response.url === tab.url) {
        showResults(response.result);
      }
    }
  );
});
