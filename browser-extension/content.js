/**
 * Content Script - Runs on every webpage
 *
 * Detects news articles and sends them to the backend for bias classification.
 */

const CONFIG = {
  API_URL: 'http://localhost:8000/api/v1',
  NEWS_DOMAINS: [
    'cnn.com', 'foxnews.com', 'nytimes.com', 'washingtonpost.com',
    'bbc.com', 'theguardian.com', 'wsj.com', 'reuters.com',
    'apnews.com', 'npr.org', 'politico.com', 'thehill.com',
    'msnbc.com', 'nbcnews.com', 'abcnews.go.com', 'cbsnews.com',
    'usatoday.com', 'latimes.com', 'nypost.com', 'dailywire.com',
    'breitbart.com', 'huffpost.com', 'vox.com', 'theatlantic.com',
    'economist.com', 'aljazeera.com',
  ],
  MIN_ARTICLE_LENGTH: 200,
};

const BIAS_COLORS = {
  'Left-Leaning': '#1565C0',
  'Center-Left': '#42A5F5',
  'Centrist': '#78909C',
  'Center-Right': '#EF5350',
  'Right-Leaning': '#C62828',
};

function isNewsSite() {
  const domain = window.location.hostname.replace('www.', '');
  return CONFIG.NEWS_DOMAINS.some(d => domain.includes(d));
}

function extractArticleContent() {
  const selectors = [
    'article', '[role="article"]', '.article-body', '.story-body',
    '.post-content', '.entry-content', 'main',
  ];

  let articleElement = null;
  for (const selector of selectors) {
    articleElement = document.querySelector(selector);
    if (articleElement) break;
  }

  if (!articleElement) return null;

  const title =
    document.querySelector('h1')?.textContent?.trim() ||
    document.title?.trim() ||
    '';

  const paragraphs = articleElement.querySelectorAll('p');
  let text = Array.from(paragraphs)
    .map(p => p.textContent.trim())
    .filter(t => t.length > 20)
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();

  if (text.length < CONFIG.MIN_ARTICLE_LENGTH) return null;

  return { title, text: text.substring(0, 5000), url: window.location.href };
}

/**
 * Call POST /api/v1/classify
 * Request:  { text, title }
 * Response: { bias, confidence, reasoning, spectrum_left, spectrum_center,
 *             spectrum_right, bias_intensity, model_used }
 */
async function classifyArticle(articleData) {
  try {
    const settings = await chrome.storage.sync.get(['apiUrl']);
    const apiUrl = settings.apiUrl || CONFIG.API_URL;

    const response = await fetch(`${apiUrl}/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: articleData.text, title: articleData.title }),
    });

    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('BiasDetector API error:', error);
    return null;
  }
}

function displayBiasBadge(result) {
  const existing = document.getElementById('bias-detector-badge');
  if (existing) existing.remove();

  const bias = result.bias || 'Centrist';
  const confidence = Math.round((result.confidence || 0) * 100);
  const color = BIAS_COLORS[bias] || '#78909C';
  const spectrumLeft = Math.round((result.spectrum_left || 0.33) * 100);
  const spectrumCenter = Math.round((result.spectrum_center || 0.34) * 100);
  const spectrumRight = Math.round((result.spectrum_right || 0.33) * 100);
  const intensity = Math.round((result.bias_intensity || 0) * 100);

  const badge = document.createElement('div');
  badge.id = 'bias-detector-badge';
  badge.className = 'bias-detector-badge';

  badge.innerHTML = `
    <div class="badge-header" style="background-color: ${color};">
      <span class="badge-title">Bias Detection</span>
      <button class="badge-close" id="bias-badge-close">&times;</button>
    </div>
    <div class="badge-content">
      <div class="bias-result">
        <div class="bias-label">${bias}</div>
        <div class="confidence-bar">
          <div class="confidence-fill" style="width: ${confidence}%; background-color: ${color};"></div>
        </div>
        <div class="confidence-text">${confidence}% confident &middot; ${result.model_used || 'ml'} model</div>
      </div>
      <div class="bias-spectrum">
        <div class="spectrum-label">Bias Spectrum</div>
        <div class="spectrum-bar">
          <div class="spectrum-left" style="width: ${spectrumLeft}%"></div>
          <div class="spectrum-center" style="width: ${spectrumCenter}%"></div>
          <div class="spectrum-right" style="width: ${spectrumRight}%"></div>
        </div>
        <div class="spectrum-labels">
          <span>Left ${spectrumLeft}%</span>
          <span>Center ${spectrumCenter}%</span>
          <span>Right ${spectrumRight}%</span>
        </div>
      </div>
      <div class="bias-details">
        <div class="detail-row">
          <span>Bias Intensity:</span>
          <span>${intensity}%</span>
        </div>
        ${result.reasoning ? `<div class="detail-row"><span>Reasoning:</span><span style="max-width:180px;text-align:right;">${result.reasoning.substring(0, 120)}</span></div>` : ''}
      </div>
    </div>
  `;

  document.body.appendChild(badge);

  document.getElementById('bias-badge-close').addEventListener('click', () => badge.remove());
  makeDraggable(badge);
}

function makeDraggable(element) {
  let pos3 = 0, pos4 = 0;
  const header = element.querySelector('.badge-header');
  if (!header) return;

  header.onmousedown = (e) => {
    e.preventDefault();
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = () => { document.onmouseup = null; document.onmousemove = null; };
    document.onmousemove = (ev) => {
      ev.preventDefault();
      element.style.top = (element.offsetTop - (pos4 - ev.clientY)) + 'px';
      element.style.left = (element.offsetLeft - (pos3 - ev.clientX)) + 'px';
      pos3 = ev.clientX;
      pos4 = ev.clientY;
    };
  };
}

async function analyzeCurrentPage() {
  const settings = await chrome.storage.sync.get(['enabled']);
  if (settings.enabled === false) return;

  if (!isNewsSite()) return;

  const articleData = extractArticleContent();
  if (!articleData) return;

  showLoadingIndicator();
  const result = await classifyArticle(articleData);
  hideLoadingIndicator();

  if (result) {
    displayBiasBadge(result);
    // Notify background to update badge icon
    chrome.runtime.sendMessage({ action: 'showBadge', bias: result.bias });
    // Store for popup retrieval
    chrome.storage.local.set({
      lastAnalysis: { url: articleData.url, result, timestamp: Date.now() },
    });
  }
}

function showLoadingIndicator() {
  const loader = document.createElement('div');
  loader.id = 'bias-detector-loader';
  loader.className = 'bias-detector-loader';
  loader.innerHTML = '<div class="spinner"></div><span>Analyzing bias...</span>';
  document.body.appendChild(loader);
}

function hideLoadingIndicator() {
  const loader = document.getElementById('bias-detector-loader');
  if (loader) loader.remove();
}

// Listen for messages from popup / background
chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  if (request.action === 'analyze') {
    analyzeCurrentPage();
    sendResponse({ status: 'analyzing' });
  } else if (request.action === 'getLastAnalysis') {
    chrome.storage.local.get(['lastAnalysis'], (data) => {
      sendResponse(data.lastAnalysis || null);
    });
    return true; // keep channel open for async
  }
});

// Auto-analyze on load if enabled
chrome.storage.sync.get(['autoAnalyze'], (data) => {
  if (data.autoAnalyze !== false) {
    setTimeout(analyzeCurrentPage, 2000);
  }
});
