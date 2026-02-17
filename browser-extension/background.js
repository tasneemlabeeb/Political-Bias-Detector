/**
 * Background Service Worker
 *
 * Handles extension lifecycle, badge updates, and context menu.
 */

const BIAS_COLORS = {
  'Left-Leaning': '#1565C0',
  'Center-Left': '#42A5F5',
  'Centrist': '#78909C',
  'Center-Right': '#EF5350',
  'Right-Leaning': '#C62828',
};

const BIAS_BADGES = {
  'Left-Leaning': 'LL',
  'Center-Left': 'CL',
  'Centrist': 'C',
  'Center-Right': 'CR',
  'Right-Leaning': 'RR',
};

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    chrome.storage.sync.set({
      enabled: true,
      autoAnalyze: true,
      apiUrl: 'http://localhost:8000/api/v1',
    });
  }

  chrome.contextMenus.create({
    id: 'analyzePage',
    title: 'Analyze for Political Bias',
    contexts: ['page'],
  });
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showBadge' && sender.tab) {
    const bias = request.bias || 'Centrist';

    chrome.action.setBadgeText({
      text: BIAS_BADGES[bias] || '?',
      tabId: sender.tab.id,
    });

    chrome.action.setBadgeBackgroundColor({
      color: BIAS_COLORS[bias] || '#78909C',
      tabId: sender.tab.id,
    });

    sendResponse({ status: 'ok' });
  }
  return true;
});

// Context menu click
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'analyzePage') {
    chrome.tabs.sendMessage(tab.id, { action: 'analyze' });
  }
});
