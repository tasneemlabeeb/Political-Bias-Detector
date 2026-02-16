/**
 * Background Service Worker
 * 
 * Handles extension lifecycle and background tasks.
 */

// Extension installed or updated
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    // First time install
    console.log('Political Bias Detector installed');
    
    // Set default settings
    chrome.storage.sync.set({
      enabled: true,
      autoAnalyze: true,
      apiUrl: 'http://localhost:8000/api/v1',
      apiKey: '',
    });
    
    // Open welcome page
    chrome.tabs.create({
      url: 'options.html',
    });
  } else if (details.reason === 'update') {
    console.log('Political Bias Detector updated');
  }
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showBadge') {
    // Update extension badge based on bias
    const biasEmojis = {
      'Left-Leaning': '◀◀',
      'Center-Left': '◀',
      'Centrist': '●',
      'Center-Right': '▶',
      'Right-Leaning': '▶▶',
    };
    
    chrome.action.setBadgeText({
      text: biasEmojis[request.bias] || '?',
      tabId: sender.tab.id,
    });
    
    // Set badge color
    const biasColors = {
      'Left-Leaning': '#1565C0',
      'Center-Left': '#42A5F5',
      'Centrist': '#78909C',
      'Center-Right': '#EF5350',
      'Right-Leaning': '#C62828',
    };
    
    chrome.action.setBadgeBackgroundColor({
      color: biasColors[request.bias] || '#78909C',
      tabId: sender.tab.id,
    });
    
    sendResponse({ status: 'Badge updated' });
  }
  
  return true;
});

// Context menu (optional)
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'analyzePage',
    title: 'Analyze for Political Bias',
    contexts: ['page'],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'analyzePage') {
    chrome.tabs.sendMessage(tab.id, { action: 'analyze' });
  }
});

console.log('Political Bias Detector: Background script loaded');
