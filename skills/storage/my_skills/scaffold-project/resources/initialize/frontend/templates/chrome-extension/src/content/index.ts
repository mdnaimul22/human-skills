// Content Script — Injects full-page overlay panel into the current page
console.log('🌐 Content script loaded on: ' + window.location.href);

const PANEL_ID = '__ext_overlay_root__';
const IFRAME_ID = '__ext_overlay_iframe__';

let isOpen = false;

function createOverlay() {
  // Prevent duplicates
  if (document.getElementById(PANEL_ID)) return;

  // Container
  const container = document.createElement('div');
  container.id = PANEL_ID;
  container.style.cssText = `
    position: fixed;
    inset: 0;
    z-index: 2147483647;
    display: flex;
    align-items: stretch;
    justify-content: stretch;
    background: transparent;
    opacity: 0;
    transition: opacity 0.25s ease;
    font-family: system-ui, sans-serif;
  `;

  // Iframe loads the full React panel
  const iframe = document.createElement('iframe');
  iframe.id = IFRAME_ID;
  iframe.src = chrome.runtime.getURL('dist/panel.html');
  iframe.allow = 'clipboard-write';
  iframe.style.cssText = `
    width: 100%;
    height: 100%;
    border: none;
    border-radius: 0;
    background: transparent;
  `;

  container.appendChild(iframe);

  // Click outside iframe to close (on the backdrop)
  container.addEventListener('click', (e) => {
    if (e.target === container) {
      destroyOverlay();
    }
  });

  // ESC to close
  const onEsc = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      destroyOverlay();
      document.removeEventListener('keydown', onEsc);
    }
  };
  document.addEventListener('keydown', onEsc);

  document.body.appendChild(container);

  // Fade in
  requestAnimationFrame(() => {
    container.style.opacity = '1';
  });

  isOpen = true;
}

function destroyOverlay() {
  const container = document.getElementById(PANEL_ID);
  if (!container) return;

  container.style.opacity = '0';
  setTimeout(() => container.remove(), 250);
  isOpen = false;
}

// Listen for toggle message from background script
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === 'TOGGLE_PANEL') {
    if (isOpen) {
      destroyOverlay();
    } else {
      createOverlay();
    }
    sendResponse({ toggled: true, isOpen: !isOpen });
  }

  if (message.action === 'CLOSE_PANEL') {
    destroyOverlay();
    sendResponse({ closed: true });
  }

  if (message.action === 'SCRAPE_PAGE_METADATA') {
    sendResponse({
      title: document.title,
      url: window.location.href,
      description: document.querySelector('meta[name="description"]')?.getAttribute('content') || '',
    });
  }
});
