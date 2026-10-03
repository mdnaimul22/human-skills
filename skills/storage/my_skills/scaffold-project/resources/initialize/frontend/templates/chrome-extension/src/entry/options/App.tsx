import React, { useState } from 'react';
import { ThemeProvider } from '@/components/layout/theme-provider';
import { UserMenu } from '@/components/layout/user-menu';
import { useChromeStorage } from '@/hooks/use-chrome-storage';
import { Settings, Shield, Server, Key, Save } from 'lucide-react';

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      <OptionsContent />
    </ThemeProvider>
  );
}

function OptionsContent() {
  const [apiUrl, setApiUrl] = useChromeStorage<string>('api_url', 'http://localhost:8000');
  const [jwtToken, setJwtToken] = useChromeStorage<string>('jwt_token', '');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  return (
    <div className="w-full min-h-screen bg-[var(--color-bg)] text-[var(--color-text)] flex flex-col font-sans selection:bg-[var(--color-primary-light)]">
      {/* Header */}
      <header className="px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-[var(--color-primary-light)] text-[var(--color-primary)]">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight">Lens Options</h1>
            <p className="text-xs text-[var(--color-text-muted)]">Customize settings, storage variables and backend servers</p>
          </div>
        </div>
      </header>

      {/* Main Settings Grid */}
      <main className="max-w-4xl w-full mx-auto p-6 flex flex-col md:flex-row gap-6">
        {/* Settings Form */}
        <form onSubmit={handleSave} className="flex-1 space-y-6">
          <div className="p-6 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] shadow-sm space-y-6">
            <div className="flex items-center gap-2 text-sm font-semibold text-[var(--color-primary)] border-b border-[var(--color-border-subtle)] pb-2">
              <Settings className="w-4.5 h-4.5" />
              <span>Core Integration Parameters</span>
            </div>

            {/* API URL Endpoint Input */}
            <div className="space-y-2">
              <label className="text-xs font-semibold flex items-center gap-1.5 text-[var(--color-text-secondary)]">
                <Server className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                <span>Backend Base Server URL</span>
              </label>
              <input
                type="url"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="w-full text-sm px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-primary)] outline-none text-[var(--color-text)] transition-colors"
                required
              />
              <span className="text-[10px] text-[var(--color-text-muted)] block">
                The target API server where background fetches are directed. Must be a valid URL.
              </span>
            </div>

            {/* JWT Secure Token Input */}
            <div className="space-y-2">
              <label className="text-xs font-semibold flex items-center gap-1.5 text-[var(--color-text-secondary)]">
                <Key className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                <span>Secure Bearer JWT Token</span>
              </label>
              <textarea
                value={jwtToken}
                onChange={(e) => setJwtToken(e.target.value)}
                placeholder="Paste JWT token here..."
                rows={3}
                className="w-full text-sm px-3 py-2 rounded bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-primary)] outline-none text-[var(--color-text)] font-mono transition-colors resize-none"
              />
              <span className="text-[10px] text-[var(--color-text-muted)] block">
                Used to authorize extension background operations. Usually managed automatically by logins.
              </span>
            </div>

            {/* Action buttons */}
            <div className="pt-2 flex items-center justify-between">
              <button
                type="submit"
                className="flex items-center gap-2 px-4 py-2 bg-[var(--color-primary)] text-[var(--color-primary-foreground)] rounded text-xs font-semibold hover:bg-[var(--color-primary-dark)] transition-colors cursor-pointer"
              >
                <Save className="w-4 h-4" />
                <span>Save Changes</span>
              </button>

              {saveSuccess && (
                <span className="text-xs text-[var(--color-success)] font-medium bg-[var(--color-success)]/10 px-3 py-1.5 rounded border border-[var(--color-success)]/20">
                  Settings synced successfully!
                </span>
              )}
            </div>
          </div>
        </form>

        {/* Sidebar Theme Panel */}
        <div className="w-full md:w-80 flex-shrink-0">
          <div className="rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] shadow-sm overflow-hidden">
            <UserMenu />
          </div>
        </div>
      </main>
    </div>
  );
}
