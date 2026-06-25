import { useState, useEffect, useRef } from 'react';
import { Settings, ChevronRight, LogOut, Check } from 'lucide-react';

/* ── Theme definitions ────────────────────────────────────── */
interface ThemeMeta { id: string; name: string; accent: string }

const THEMES: ThemeMeta[] = [
  { id: 'dark', name: 'Default', accent: '#3b82f6' },
  { id: 'matrix', name: 'Matrix', accent: '#10b981' },
  { id: 'cream', name: 'Monokai', accent: '#a6e22e' },
  { id: 'matte-black', name: 'VS Code', accent: '#007acc' },
  { id: 'black-brown', name: 'Dracula', accent: '#bd93f9' },
  { id: 'jam-black', name: 'One Dark', accent: '#61afef' },
  { id: 'jam-navy', name: 'Nord', accent: '#88c0d0' },
  { id: 'light', name: 'Clear Ice', accent: '#1d4ed8' },
  { id: 'snow', name: 'Snow', accent: '#3b82f6' },
  { id: 'claude', name: 'Warm Light', accent: '#d97706' },
];

/* ── Font definitions ─────────────────────────────────────── */
interface FontDef { key: string; label: string; family: string }

const FONTS: FontDef[] = [
  { key: 'system', label: 'System', family: "system-ui, -apple-system, 'Segoe UI', sans-serif" },
  { key: 'inter', label: 'Inter', family: "'Inter', system-ui, sans-serif" },
  { key: 'poppins', label: 'Poppins', family: "'Poppins', system-ui, sans-serif" },
  { key: 'roboto', label: 'Roboto', family: "'Roboto', system-ui, sans-serif" },
  { key: 'outfit', label: 'Outfit', family: "'Outfit', system-ui, sans-serif" },
  { key: 'space-grotesk', label: 'Space Grotesk', family: "'Space Grotesk', system-ui, sans-serif" },
];

/* ── Scale definitions ────────────────────────────────────── */
interface ScaleDef { key: string; label: string; size: string }

const SCALES: ScaleDef[] = [
  { key: 's', label: 'S', size: '14px' },
  { key: 'm', label: 'M', size: '16px' },
  { key: 'l', label: 'L', size: '18px' },
  { key: 'xl', label: 'XL', size: '20px' },
];

/* ── Theme provider hook (uses data-theme attribute) ──────── */
export function useTheme() {
  const [theme, setThemeState] = useState(() => {
    try {
      return localStorage.getItem('ext-theme') || 'dark';
    } catch { return 'dark'; }
  });

  const setTheme = (id: string) => {
    setThemeState(id);
    document.documentElement.setAttribute('data-theme', id);
    try { localStorage.setItem('ext-theme', id); } catch {}
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, []);

  return { theme, setTheme };
}

/* ── Settings store (localStorage) ────────────────────────── */
function useSettings() {
  const [fontKey, setFontKeyState] = useState(() => {
    try { return localStorage.getItem('ext-font') || 'system'; } catch { return 'system'; }
  });
  const [scaleKey, setScaleKeyState] = useState(() => {
    try { return localStorage.getItem('ext-scale') || 'm'; } catch { return 'm'; }
  });

  const setFont = (key: string) => {
    setFontKeyState(key);
    try { localStorage.setItem('ext-font', key); } catch {}
    const font = FONTS.find(f => f.key === key) ?? FONTS[0];
    if (key !== 'system') {
      document.documentElement.style.setProperty('--font-sans', font.family);
    } else {
      document.documentElement.style.removeProperty('--font-sans');
    }
  };

  const setScale = (key: string) => {
    setScaleKeyState(key);
    try { localStorage.setItem('ext-scale', key); } catch {}
    const scale = SCALES.find(s => s.key === key) ?? SCALES[1];
    if (key !== 'm') {
      document.documentElement.style.fontSize = scale.size;
    } else {
      document.documentElement.style.removeProperty('font-size');
    }
  };

  // Apply on mount
  useEffect(() => {
    if (fontKey !== 'system') {
      const font = FONTS.find(f => f.key === fontKey) ?? FONTS[0];
      document.documentElement.style.setProperty('--font-sans', font.family);
    }
    if (scaleKey !== 'm') {
      const scale = SCALES.find(s => s.key === scaleKey) ?? SCALES[1];
      document.documentElement.style.fontSize = scale.size;
    }
  }, []);

  return { fontKey, scaleKey, setFont, setScale };
}

/* ── Submenu Component ────────────────────────────────────── */
function Submenu({ trigger, children }: { trigger: React.ReactNode; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <div onClick={() => setOpen(o => !o)}>{trigger}</div>
      {open && (
        <div className="absolute left-full top-0 ml-1 min-w-[160px] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-lg py-1 z-50 max-h-72 overflow-y-auto">
          {children}
        </div>
      )}
    </div>
  );
}

/* ── UserMenu Component ───────────────────────────────────── */
export function UserMenu({ collapsed = false }: { collapsed?: boolean } = {}) {
  const { theme, setTheme } = useTheme();
  const { fontKey, scaleKey, setFont, setScale } = useSettings();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const currentTheme = THEMES.find(t => t.id === theme) ?? THEMES[0];
  const currentFont = FONTS.find(f => f.key === fontKey) ?? FONTS[0];

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div ref={menuRef} className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setOpen(o => !o)}
        className={`w-full flex items-center rounded-lg transition-all text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-primary-light)] cursor-pointer outline-none ${
          collapsed ? 'justify-center py-2 px-0' : 'gap-3 px-3 py-2.5'
        }`}
      >
        <div className="w-8 h-8 rounded-full bg-[var(--color-primary)] shrink-0 flex items-center justify-center text-[var(--color-primary-foreground)] text-sm font-bold">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
        {!collapsed && (
          <div className="flex flex-col items-start min-w-0 flex-1">
            <span className="text-sm font-medium truncate w-full text-left">Guest</span>
            <span className="text-xs text-[var(--color-text-muted)] truncate w-full text-left">Settings & Profile</span>
          </div>
        )}
      </button>

      {/* Dropdown Panel */}
      {open && (
        <div className={`absolute bottom-full mb-2 w-64 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-lg overflow-visible z-50 ${
          collapsed ? 'left-14' : 'left-0'
        }`}>
          {/* User Info */}
          <div className="px-3 py-2 border-b border-[var(--color-border)]">
            <span className="text-sm font-medium text-[var(--color-text)]">Guest</span>
          </div>

          {/* Settings Label */}
          <div className="px-3 pt-2 pb-1">
            <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Settings</span>
          </div>

          {/* Theme Row */}
          <div className="flex items-center justify-between px-3 py-1.5 text-sm hover:bg-[var(--color-primary-light)] transition-colors rounded-md mx-1">
            <button
              onClick={() => {
                const idx = THEMES.findIndex(t => t.id === theme);
                setTheme(THEMES[(idx + 1) % THEMES.length].id);
              }}
              className="flex items-center gap-2 text-[var(--color-text)] flex-1 text-left cursor-pointer outline-none py-0.5"
            >
              <Settings className="w-4 h-4 text-[var(--color-text-secondary)]" />
              <span className="text-sm font-medium">Theme</span>
            </button>
            <div className="flex items-center gap-0">
              <button
                onClick={() => {
                  const idx = THEMES.findIndex(t => t.id === theme);
                  setTheme(THEMES[(idx + 1) % THEMES.length].id);
                }}
                className="flex items-center gap-1.5 bg-[var(--color-bg)] hover:bg-[var(--color-primary-light)] border border-r-0 border-[var(--color-border)] rounded-l-md px-2.5 h-7 transition-colors text-xs text-[var(--color-text-secondary)] font-semibold cursor-pointer outline-none"
              >
                <span className="w-2.5 h-2.5 rounded-full ring-1 ring-[var(--color-border)]" style={{ backgroundColor: currentTheme.accent }} />
                <span>{currentTheme.name}</span>
              </button>
              <Submenu
                trigger={
                  <button className="bg-[var(--color-bg)] hover:bg-[var(--color-primary-light)] border border-[var(--color-border)] rounded-r-md px-2 h-7 transition-colors cursor-pointer text-[var(--color-text-muted)] flex items-center justify-center outline-none">
                    <ChevronRight className="w-3 h-3" />
                  </button>
                }
              >
                {THEMES.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-[var(--color-primary-light)] transition-colors cursor-pointer text-left outline-none"
                  >
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: t.accent }} />
                    <span className="flex-1 text-[var(--color-text)]">{t.name}</span>
                    {theme === t.id && <Check className="w-4 h-4 text-[var(--color-primary)]" />}
                  </button>
                ))}
              </Submenu>
            </div>
          </div>

          {/* Font Family Row */}
          <div className="flex items-center justify-between px-3 py-1.5 text-sm hover:bg-[var(--color-primary-light)] transition-colors rounded-md mx-1">
            <button
              onClick={() => {
                const idx = FONTS.findIndex(f => f.key === fontKey);
                setFont(FONTS[(idx + 1) % FONTS.length].key);
              }}
              className="flex items-center gap-2 text-[var(--color-text)] flex-1 text-left cursor-pointer outline-none py-0.5"
            >
              <svg className="w-4 h-4 text-[var(--color-text-secondary)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 21V3l8 9 8-9v18" />
              </svg>
              <span className="text-sm font-medium">Font Family</span>
            </button>
            <div className="flex items-center gap-0">
              <button
                onClick={() => {
                  const idx = FONTS.findIndex(f => f.key === fontKey);
                  setFont(FONTS[(idx + 1) % FONTS.length].key);
                }}
                className="flex items-center bg-[var(--color-bg)] hover:bg-[var(--color-primary-light)] border border-r-0 border-[var(--color-border)] rounded-l-md px-2.5 h-7 transition-colors text-xs text-[var(--color-text-secondary)] font-semibold cursor-pointer outline-none"
                style={{ fontFamily: currentFont.family }}
              >
                <span>{currentFont.label}</span>
              </button>
              <Submenu
                trigger={
                  <button className="bg-[var(--color-bg)] hover:bg-[var(--color-primary-light)] border border-[var(--color-border)] rounded-r-md px-2 h-7 transition-colors cursor-pointer text-[var(--color-text-muted)] flex items-center justify-center outline-none">
                    <ChevronRight className="w-3 h-3" />
                  </button>
                }
              >
                {FONTS.map(f => (
                  <button
                    key={f.key}
                    onClick={() => setFont(f.key)}
                    className="w-full flex items-center justify-between px-3 py-1.5 text-sm hover:bg-[var(--color-primary-light)] transition-colors cursor-pointer text-left outline-none"
                    style={{ fontFamily: f.family }}
                  >
                    <span className="flex-1 text-[var(--color-text)]">{f.label}</span>
                    {fontKey === f.key && <Check className="w-4 h-4 text-[var(--color-primary)]" />}
                  </button>
                ))}
              </Submenu>
            </div>
          </div>

          {/* Size Row */}
          <div className="flex items-center justify-between px-3 py-1.5 mx-1">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-[var(--color-text-secondary)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M4 7V4h16v3" />
                <path d="M9 20h6" />
                <path d="M12 4v16" />
              </svg>
              <span className="text-sm font-medium text-[var(--color-text)]">Size</span>
            </div>
            <div className="flex items-center gap-0.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-md p-0.5">
              {SCALES.map(s => (
                <button
                  key={s.key}
                  onClick={() => setScale(s.key)}
                  className={`text-[10px] uppercase px-2 py-1 rounded-md transition-all font-bold cursor-pointer outline-none ${
                    scaleKey === s.key
                      ? 'bg-[var(--color-card)] shadow-sm text-[var(--color-primary)] border border-[var(--color-border)]'
                      : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Separator + Logout */}
          <div className="border-t border-[var(--color-border)] mt-1">
            <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10 transition-colors cursor-pointer outline-none">
              <LogOut className="w-4 h-4" />
              <span>Log out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
