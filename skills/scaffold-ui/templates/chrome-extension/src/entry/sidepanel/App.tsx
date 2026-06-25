import { useState } from 'react';
import { ThemeProvider } from '@/components/layout/theme-provider';
import { UserMenu } from '@/components/layout/user-menu';
import { LayoutGrid, FileText, Layers, Bell, Shield } from 'lucide-react';

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      <SidePanelContent />
    </ThemeProvider>
  );
}

function SidePanelContent() {
  const [activeTab, setActiveTab] = useState<'metrics' | 'logs'>('metrics');

  return (
    <div className="w-full min-h-screen bg-[var(--color-bg)] text-[var(--color-text)] flex flex-col font-sans selection:bg-[var(--color-primary-light)]">
      {/* Header */}
      <header className="px-4 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1 rounded bg-[var(--color-primary-light)] text-[var(--color-primary)]">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight">Lens Hub</h1>
            <p className="text-[10px] text-[var(--color-text-muted)]">Chrome Workspace Side Panel</p>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="flex gap-1 p-0.5 rounded-md bg-[var(--color-input)] border border-[var(--color-border-subtle)]">
          <button
            onClick={() => setActiveTab('metrics')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs rounded transition-all cursor-pointer ${
              activeTab === 'metrics'
                ? 'bg-[var(--color-surface)] text-[var(--color-text)] font-semibold shadow-sm'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            <span>Overview</span>
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs rounded transition-all cursor-pointer ${
              activeTab === 'logs'
                ? 'bg-[var(--color-surface)] text-[var(--color-text)] font-semibold shadow-sm'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Process Logs</span>
          </button>
        </div>
      </header>

      {/* Main Panel Content */}
      <main className="flex-1 p-4 flex flex-col gap-4 overflow-y-auto">
        {activeTab === 'metrics' ? (
          <>
            {/* Project Specs */}
            <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-primary)] border-b border-[var(--color-border-subtle)] pb-2">
                <Layers className="w-4 h-4" />
                <span>Structural Modules</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs pt-1">
                <div className="p-3 rounded bg-[var(--color-bg)] border border-[var(--color-border-subtle)]">
                  <span className="text-[var(--color-text-muted)] text-[10px] block">Popup Layer</span>
                  <span className="font-semibold mt-1 block">Active</span>
                </div>
                <div className="p-3 rounded bg-[var(--color-bg)] border border-[var(--color-border-subtle)]">
                  <span className="text-[var(--color-text-muted)] text-[10px] block">Side Panel</span>
                  <span className="font-semibold mt-1 block">Active</span>
                </div>
              </div>
            </div>

            {/* Notification alert banner */}
            <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-primary)] border-b border-[var(--color-border-subtle)] pb-2">
                <Bell className="w-4 h-4" />
                <span>Notifications</span>
              </div>
              <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
                Chrome Extension Presentation Layer initialized. Scrapes are mapped through background script endpoints.
              </p>
            </div>
          </>
        ) : (
          <div className="p-4 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] shadow-sm flex-1 flex flex-col">
            <div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-primary)] border-b border-[var(--color-border-subtle)] pb-2 mb-3">
              <FileText className="w-4 h-4" />
              <span>Real-time Stream Console</span>
            </div>
            <div className="flex-1 bg-[var(--color-bg)] border border-[var(--color-border)] p-3 rounded font-mono text-[10px] text-[var(--color-text-secondary)] space-y-2 overflow-y-auto min-h-[250px]">
              <div><span className="text-emerald-500">[SYSTEM]</span> Extension context bound.</div>
              <div><span className="text-blue-500">[INFO]</span> Listening to active runtime ports.</div>
              <div><span className="text-amber-500">[WARN]</span> Local mock server in use (No default API url).</div>
            </div>
          </div>
        )}
      </main>

      {/* Theme selector widget */}
      <UserMenu />
    </div>
  );
}
