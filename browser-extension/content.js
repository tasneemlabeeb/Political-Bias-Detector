/**
 * Content Script - Runs on every webpage
 * 
 * Detects news articles and analyzes them for political bias.
 */

// Configuration
const CONFIG = {
  API_URL: 'http://localhost:8000/api/v1',
  // News domains to analyze
  NEWS_DOMAINS: [
    'cnn.com',
    'foxnews.com',
    'nytimes.com',
    'washingtonpost.com',
    'bbc.com',
    'theguardian.com',
    'wsj.com',
    'reuters.com',
    'apnews.com',
    'npr.org',
    'politico.com',
    'thehill.com',
  ],
  MIN_ARTICLE_LENGTH: 200,
};

// Check if current domain is a news site
function isNewsSite() {
  const domain = window.location.hostname.replace('www.', '');
  return CONFIG.NEWS_DOMAINS.some(newsDomain => domain.includes(newsDomain));
}

// Extract article content from page
function extractArticleContent() {
  // Try common article selectors
  const selectors = [
    'article',
    '[role="article"]',
    '.article-body',
    '.story-body',
    '.post-content',
    '.entry-content',
    'main',
  ];

  let articleElement = null;
  for (const selector of selectors) {
    articleElement = document.querySelector(selector);
    if (articleElement) break;
  }

  if (!articleElement) {
    console.log('BiasDetector: No article element found');
    return null;
  }

  // Extract title
  let title = document.querySelector('h1')?.textContent?.trim() || 
              document.querySelector('title')?.textContent?.trim() || 
              '';

  // Extract article text
  const paragraphs = articleElement.querySelectorAll('p');
  let text = Array.from(paragraphs)
    .map(p => p.textContent.trim())
    .filter(t => t.length > 20)
    .join(' ');

  // Clean up text
  text = text.replace(/\s+/g, ' ').trim();

  if (text.length < CONFIG.MIN_ARTICLE_LENGTH) {
    console.log('BiasDetector: Article too short');
    return null;
  }

  return {
    title: title,
    text: text.substring(0, 5000), // Limit to 5000 chars
    url: window.location.href,
  };
}

// Call API to classify article
async function classifyArticle(articleData) {
  try {
    const settings = await chrome.storage.sync.get(['apiUrl', 'apiKey']);
    const apiUrl = settings.apiUrl || CONFIG.API_URL;
    const apiKey = settings.apiKey;

    const response = await fetch(`${apiUrl}/classify/text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey && { 'X-API-Key': apiKey }),
      },
      body: JSON.stringify({
        text: articleData.text,
        title: articleData.title,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('BiasDetector API error:', error);
    return null;
  }
}

// Display bias badge on page
function displayBiasBadge(result) {
  // Remove existing badge if any
  const existingBadge = document.getElementById('bias-detector-badge');
  if (existingBadge) {
    existingBadge.remove();
  }

  // Create badge
  const badge = document.createElement('div');
  badge.id = 'bias-detector-badge';
  badge.className = 'bias-detector-badge';
  
  // Set color based on bias
  const biasColors = {
    'Left-Leaning': '#1565C0',
    'Center-Left': '#42A5F5',
    'Centrist': '#78909C',
    'Center-Right': '#EF5350',
    'Right-Leaning': '#C62828',
  };
  
  const color = biasColors[result.bias_label] || '#78909C';
  const confidence = Math.round(result.confidence * 100);
  
  badge.innerHTML = `
    <div class="badge-header" style="background-color: ${color};">
      <span class="badge-icon">📊</span>
      <span class="badge-title">Bias Detection</span>
      <button class="badge-close" id="bias-badge-close">×</button>
    </div>
    <div class="badge-content">
      <div class="bias-result">
        <div class="bias-label">${result.bias_label}</div>
        <div class="confidence-bar">
          <div class="confidence-fill" style="width: ${confidence}%; background-color: ${color};"></div>
        </div>
        <div class="confidence-text">${confidence}% confident</div>
      </div>
      <div class="bias-spectrum">
        <div class="spectrum-label">Bias Spectrum</div>
        <div class="spectrum-bar">
          <div class="spectrum-left" style="width: ${result.spectrum.left * 100}%"></div>
          <div class="spectrum-center" style="width: ${result.spectrum.center * 100}%"></div>
          <div class="spectrum-right" style="width: ${result.spectrum.right * 100}%"></div>
        </div>
        <div class="spectrum-labels">
          <span>Left</span>
          <span>Center</span>
          <span>Right</span>
        </div>
      </div>
      <div class="bias-details">
        <div class="detail-row">
          <span>Direction Score:</span>
          <span>${result.direction_score.toFixed(2)}</span>
        </div>
        <div class="detail-row">
          <span>Intensity:</span>
          <span>${Math.round(result.intensity_score * 100)}%</span>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(badge);
  
  // Add close handler
  document.getElementById('bias-badge-close').addEventListener('click', () => {
    badge.remove();
  });
  
  // Make badge draggable
  makeDraggable(badge);
}

// Make element draggable
function makeDraggable(element) {
  let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
  const header = element.querySelector('.badge-header');
  
  if (header) {
    header.onmousedown = dragMouseDown;
  }
  
  function dragMouseDown(e) {
    e.preventDefault();
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = closeDragElement;
    document.onmousemove = elementDrag;
  }
  
  function elementDrag(e) {
    e.preventDefault();
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    element.style.top = (element.offsetTop - pos2) + 'px';
    element.style.left = (element.offsetLeft - pos1) + 'px';
  }
  
  function closeDragElement() {
    document.onmouseup = null;
    document.onmousemove = null;
  }
}

// Main function
async function analyzeCurrentPage() {
  // Check if extension is enabled
  const settings = await chrome.storage.sync.get(['enabled']);
  if (settings.enabled === false) {
    return;
  }
  
  // Check if this is a news site
  if (!isNewsSite()) {
    console.log('BiasDetector: Not a news site');
    return;
  }
  
  // Extract article
  const articleData = extractArticleContent();
  if (!articleData) {
    return;
  }
  
  console.log('BiasDetector: Analyzing article...', articleData.title);
  
  // Show loading indicator
  showLoadingIndicator();
  
  // Classify article
  const result = await classifyArticle(articleData);
  
  // Hide loading indicator
  hideLoadingIndicator();
  
  if (result) {
    console.log('BiasDetector: Result:', result);
    displayBiasBadge(result);
    
    // Store result
    chrome.storage.local.set({
      lastAnalysis: {
        url: articleData.url,
        result: result,
        timestamp: Date.now(),
      },
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
  if (loader) {
    loader.remove();
  }
}

// Listen for messages from popup/background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyze') {
    analyzeCurrentPage();
    sendResponse({ status: 'analyzing' });
  } else if (request.action === 'getLastAnalysis') {
    chrome.storage.local.get(['lastAnalysis'], (data) => {
      sendResponse(data.lastAnalysis);
    });
    return true; // Keep channel open for async response
  }
});

console.log('BiasDetector: Content script loaded');

// Auto-analyze after page load (if enabled in settings)
chrome.storage.sync.get(['autoAnalyze'], (data) => {
  if (data.autoAnalyze !== false) {
    // Wait a bit for page to fully load
    setTimeout(analyzeCurrentPage, 2000);
  }
});
