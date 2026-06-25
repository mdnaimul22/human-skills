import { useState, useEffect } from 'react';
import { ThemeProvider } from '@/components/layout/theme-provider';
import { UserMenu } from '@/components/layout/user-menu';
import { Shield, Globe, Terminal, RefreshCw } from 'lucide-react';

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      <PopupContent />
    </ThemeProvider>
  );
}

function PopupContent() {
  const [metadata, setMetadata] = useState<{ title: string; url: string; h1: string; description: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scrapeCurrentTab = () => {
    setLoading(true);
    setError(null);

    if (typeof chrome === 'undefined' || !chrome.tabs) {
      setTimeout(() => {
        setMetadata({
          title: "Demo Page Title",
          url: "https://example.com/demo-path",
          h1: "Example Heading 1",
          description: "This is a placeholder description because the extension is running outside Chrome environment."
        });
        setLoading(false);
      }, 800);
      return;
    }

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0];
      if (!activeTab?.id) {
        setError("No active tab found.");
        setLoading(false);
        return;
      }

      chrome.tabs.sendMessage(activeTab.id, { action: 'SCRAPE_PAGE_METADATA' }, (response) => {
        setLoading(false);
        if (chrome.runtime.lastError) {
          setError("Cannot inspect this page. Make sure the content script is injected.");
          return;
        }
        if (response && response.success) {
          setMetadata(response.metadata);
        } else {
          setError(response?.error || "Failed to inspect page.");
        }
      });
    });
  };

  useEffect(() => {
    scrapeCurrentTab();
  }, []);

  return (
    <div className="w-[380px] min-h-[480px] bg-[var(--color-bg)] text-[var(--color-text)] flex flex-col font-sans selection:bg-[var(--color-primary-light)]">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-[var(--color-primary-light)] text-[var(--color-primary)]">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight">Chrome Lens</h1>
            <p className="text-[10px] text-[var(--color-text-muted)]">Presentation Layer Client</p>
          </div>
        </div>
        <button
          onClick={scrapeCurrentTab}
          disabled={loading}
          className="p-1.5 rounded-full hover:bg-[var(--color-input)] transition-colors border border-[var(--color-border-subtle)] cursor-pointer text-[var(--color-text-secondary)] disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-4 flex flex-col gap-4 overflow-y-auto">
        <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] shadow-sm">
          <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-[var(--color-primary)]">
            <Globe className="w-4 h-4" />
            <span>Active Webpage Scope</span>
          </div>

          {error && (
            <div className="text-xs text-[var(--color-danger)] bg-[var(--color-danger)]/10 p-2.5 rounded border border-[var(--color-danger)]/20">
              {error}
            </div>
          )}

          {metadata ? (
            <div className="space-y-3 mt-1 text-xs">
              <div>
                <span className="text-[var(--color-text-muted)] block text-[10px] uppercase font-medium">Page Title</span>
                <p className="text-[var(--color-text)] font-medium leading-relaxed truncate">{metadata.title}</p>
              </div>
              <div>
                <span className="text-[var(--color-text-muted)] block text-[10px] uppercase font-medium">Domain URL</span>
                <p className="text-[var(--color-primary)] font-mono truncate">{metadata.url}</p>
              </div>
              {metadata.h1 && (
                <div>
                  <span className="text-[var(--color-text-muted)] block text-[10px] uppercase font-medium">Primary Header (H1)</span>
                  <p className="text-[var(--color-text)] italic truncate">"{metadata.h1}"</p>
                </div>
              )}
            </div>
          ) : (
            !error && <div className="h-20 flex items-center justify-center text-xs text-[var(--color-text-muted)]">Gathering metrics...</div>
          )}
        </div>

        {/* Backend Connectivity Status */}
        <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] shadow-sm">
          <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-[var(--color-primary)]">
            <Terminal className="w-4 h-4" />
            <span>Local API Integration</span>
          </div>
          <div className="flex items-center justify-between text-xs mt-1">
            <span className="text-[var(--color-text-secondary)]">Endpoint status</span>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-[var(--color-text-secondary)] font-medium">Connected</span>
            </div>
          </div>
        </div>
      </main>

      {/* User settings menu containing theme selectors */}
      <UserMenu />
    </div>
  );
}
