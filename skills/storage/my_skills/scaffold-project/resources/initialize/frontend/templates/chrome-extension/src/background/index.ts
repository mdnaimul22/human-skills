// Background Service Worker — handles extension icon click
console.log('🚀 Background Service Worker initialized.');

// URLs where content scripts cannot run
const RESTRICTED_URL_PREFIXES = [
  'chrome://',
  'chrome-extension://',
  'about:',
  'edge://',
  'brave://',
];

function isRestrictedUrl(url: string | undefined): boolean {
  if (!url) return true;
  return RESTRICTED_URL_PREFIXES.some((prefix) => url.startsWith(prefix));
}

// When user clicks the extension icon → tell content script to toggle overlay
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id || isRestrictedUrl(tab.url)) {
    console.warn('⚠️ Cannot run on this page:', tab.url);
    return;
  }

  try {
    await chrome.tabs.sendMessage(tab.id, { action: 'TOGGLE_PANEL' });
  } catch {
    // Content script not responding — inject it first, then retry
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['dist/content.js'],
      });
      setTimeout(() => {
        chrome.tabs.sendMessage(tab.id!, { action: 'TOGGLE_PANEL' });
      }, 300);
    } catch (injectErr) {
      console.warn('⚠️ Cannot inject script on this page:', injectErr);
    }
  }
});

// Listen for messages from panel / content scripts
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  const { action, payload } = message;

  switch (action) {
    case 'GET_STORAGE':
      chrome.storage.local.get(payload.key, (result) => {
        sendResponse({ value: result[payload.key] ?? null });
      });
      return true;

    case 'SET_STORAGE':
      chrome.storage.local.set({ [payload.key]: payload.value }, () => {
        sendResponse({ success: true });
      });
      return true;

    case 'GET_TAB_INFO':
      if (_sender.tab) {
        sendResponse({
          url: _sender.tab.url,
          title: _sender.tab.title,
          favIconUrl: _sender.tab.favIconUrl,
        });
      }
      return true;

    default:
      sendResponse({ error: `Unknown action: ${action}` });
      return false;
  }
});
