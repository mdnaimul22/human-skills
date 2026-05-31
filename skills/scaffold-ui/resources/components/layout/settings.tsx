"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useTheme } from "next-themes";
import { useEffect, useRef, useState } from "react";

/* ── Font & Scale definitions ────────────────────────────── */

interface FontDef {
    key: string;
    label: string;
    family: string;
}

const FONTS: FontDef[] = [
    { key: "system", label: "System", family: "system-ui, -apple-system, 'Segoe UI', sans-serif" },
    { key: "inter", label: "Inter", family: "var(--font-sans), system-ui, sans-serif" },
    { key: "poppins", label: "Poppins", family: "var(--font-poppins), system-ui, sans-serif" },
    { key: "roboto", label: "Roboto", family: "var(--font-roboto), system-ui, sans-serif" },
];

interface ScaleDef {
    key: string;
    label: string;
    size: string;
}

const SCALES: ScaleDef[] = [
    { key: "s", label: "S", size: "14px" },
    { key: "m", label: "M", size: "16px" },
    { key: "l", label: "L", size: "18px" },
    { key: "xl", label: "XL", size: "20px" },
];

/* ── Theme definitions ────────────────────────────────────── */

interface ThemeMeta {
    id: string;
    name: string;
    accent: string;
}

const THEMES: ThemeMeta[] = [
    { id: "dark", name: "Default", accent: "#3b82f6" },
    { id: "matrix", name: "Matrix", accent: "#10b981" },
    { id: "cream", name: "Monokai", accent: "#a6e22e" },
    { id: "matte-black", name: "VS Code", accent: "#007acc" },
    { id: "black-brown", name: "Dracula", accent: "#bd93f9" },
    { id: "jam-black", name: "One Dark", accent: "#61afef" },
    { id: "jam-navy", name: "Nord", accent: "#88c0d0" },
    { id: "light", name: "Clear Ice", accent: "#1d4ed8" },
    { id: "snow", name: "Snow", accent: "#3b82f6" },
];

/* ── Zustand store (persisted to localStorage) ───────────── */

interface AppSettingsState {
    fontKey: string;
    scaleKey: string;
    setFont: (key: string) => void;
    setScale: (key: string) => void;
}

export const useAppSettings = create<AppSettingsState>()(
    persist(
        (set) => ({
            fontKey: "system",
            scaleKey: "m",
            setFont: (key: string) => set({ fontKey: key }),
            setScale: (key: string) => set({ scaleKey: key }),
        }),
        {
            name: "app-settings",
        },
    ),
);

/* ── Side-effect: apply font + scale to <html> ───────────── */

function useApplySettings() {
    const { fontKey, scaleKey } = useAppSettings();

    useEffect(() => {
        const font = FONTS.find((f) => f.key === fontKey) ?? FONTS[0];
        const scale = SCALES.find((s) => s.key === scaleKey) ?? SCALES[1];

        document.documentElement.style.setProperty("--font-primary", font.family);
        document.documentElement.style.fontSize = scale.size;
    }, [fontKey, scaleKey]);
}

/* ── Settings Panel Component ────────────────────────────── */

interface SettingsPanelProps {
    collapsed?: boolean;
}

export function SettingsPanel({ collapsed = false }: SettingsPanelProps) {
    const { fontKey, scaleKey, setFont, setScale } = useAppSettings();
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);
    const [open, setOpen] = useState(false);
    const [fontMenuOpen, setFontMenuOpen] = useState(false);
    const [themeMenuOpen, setThemeMenuOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => setMounted(true), []);

    // Apply settings to DOM
    useApplySettings();

    // Close on outside click
    useEffect(() => {
        if (!open) return;
        function handler(e: MouseEvent) {
            if (ref.current && !ref.current.contains(e.target as Node)) {
                setOpen(false);
                setFontMenuOpen(false);
                setThemeMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, [open]);

    const currentFont = FONTS.find((f) => f.key === fontKey) ?? FONTS[0];
    const currentTheme = mounted
        ? (THEMES.find((t) => t.id === theme) ?? THEMES[0])
        : THEMES[0];

    return (
        <div className="relative" ref={ref}>
            {/* Settings trigger button */}
            <button
                onClick={() => { setOpen(!open); setFontMenuOpen(false); setThemeMenuOpen(false); }}
                className={`
                    w-full flex items-center gap-3 rounded-lg transition-all
                    text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-primary-light)]
                    ${collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2.5"}
                `}
                title="Settings"
            >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
                </svg>
                {!collapsed && <span className="text-sm font-medium truncate">Settings</span>}
            </button>

            {/* Popup panel */}
            {open && (
                <div
                    className={`
                        absolute z-[100] w-60
                        bg-[var(--color-card)] border border-[var(--color-border)]
                        rounded-xl shadow-lg py-2
                        ${collapsed
                            ? "left-full bottom-0 ml-2"
                            : "bottom-full left-0 mb-2"
                        }
                    `}
                >
                    <div className="px-4 py-2 space-y-3">
                        {/* ── Font Scale ── */}
                        <div className="flex items-center justify-between gap-2">
                            <span className="text-xs text-[var(--color-text-muted)] flex items-center gap-1.5 font-medium">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                    <path d="M4 7V4h16v3" />
                                    <path d="M9 20h6" />
                                    <path d="M12 4v16" />
                                </svg>
                                Size
                            </span>
                            <div className="flex items-center gap-0.5 bg-[var(--color-bg)] rounded-md p-0.5">
                                {SCALES.map((s) => (
                                    <button
                                        key={s.key}
                                        onClick={() => setScale(s.key)}
                                        className={`text-[10px] uppercase px-2 py-1 rounded-sm transition-colors font-semibold ${scaleKey === s.key
                                                ? "bg-[var(--color-card)] shadow-sm text-[var(--color-primary)]"
                                                : "text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
                                            }`}
                                    >
                                        {s.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* ── Font Family (hover submenu) ── */}
                        <div
                            className="relative"
                            onMouseEnter={() => { setFontMenuOpen(true); setThemeMenuOpen(false); }}
                            onMouseLeave={() => setFontMenuOpen(false)}
                        >
                            <div
                                className="flex items-center justify-between gap-2 cursor-pointer py-1"
                                onClick={() => {
                                    const idx = FONTS.findIndex((f) => f.key === fontKey);
                                    setFont(FONTS[(idx + 1) % FONTS.length].key);
                                }}
                            >
                                <span className="text-xs text-[var(--color-text-muted)] flex items-center gap-1.5 font-medium">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M4 21V3l8 9 8-9v18" />
                                    </svg>
                                    Font
                                </span>
                                <div className="flex items-center gap-1">
                                    <span className="text-[10px] text-[var(--color-text-muted)]">{currentFont.label}</span>
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                        <path d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </div>

                            {/* Font submenu */}
                            {fontMenuOpen && (
                                <div className="absolute bottom-0 left-full pl-1 z-[110]">
                                    <div className="w-44 bg-[var(--color-card)] rounded-xl shadow-xl border border-[var(--color-border)] py-1">
                                        {FONTS.map((f) => (
                                            <button
                                                key={f.key}
                                                onClick={() => { setFont(f.key); setFontMenuOpen(false); }}
                                                className={`w-full text-left px-4 py-2 text-xs hover:bg-[var(--color-primary-light)] transition-colors flex items-center justify-between ${fontKey === f.key
                                                        ? "text-[var(--color-primary)] font-bold"
                                                        : "text-[var(--color-text)]"
                                                    }`}
                                                style={{ fontFamily: f.family }}
                                            >
                                                <span>{f.label}</span>
                                                {fontKey === f.key && (
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M20 6L9 17l-5-5" />
                                                    </svg>
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* ── Theme (hover submenu) ── */}
                        <div
                            className="relative"
                            onMouseEnter={() => { setThemeMenuOpen(true); setFontMenuOpen(false); }}
                            onMouseLeave={() => setThemeMenuOpen(false)}
                        >
                            <div
                                className="flex items-center justify-between gap-2 cursor-pointer py-1"
                                onClick={() => {
                                    const idx = THEMES.findIndex((t) => t.id === theme);
                                    setTheme(THEMES[(idx + 1) % THEMES.length].id);
                                }}
                            >
                                <span className="text-xs text-[var(--color-text-muted)] flex items-center gap-1.5 font-medium">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <circle cx="12" cy="12" r="5" />
                                        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                                    </svg>
                                    Theme
                                </span>
                                <div className="flex items-center gap-1">
                                    <span
                                        className="w-2.5 h-2.5 rounded-full ring-1 ring-[var(--color-border)]"
                                        style={{ backgroundColor: currentTheme.accent }}
                                    />
                                    <span className="text-[10px] text-[var(--color-text-muted)]">{currentTheme.name}</span>
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                        <path d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </div>

                            {/* Theme submenu */}
                            {themeMenuOpen && mounted && (
                                <div className="absolute bottom-0 left-full pl-1 z-[110]">
                                    <div className="w-48 bg-[var(--color-card)] rounded-xl shadow-xl border border-[var(--color-border)] py-1 max-h-72 overflow-y-auto">
                                        {THEMES.map((t) => (
                                            <button
                                                key={t.id}
                                                onClick={() => { setTheme(t.id); setThemeMenuOpen(false); }}
                                                className={`w-full text-left px-4 py-2 text-xs hover:bg-[var(--color-primary-light)] transition-colors flex items-center gap-2.5 ${theme === t.id
                                                        ? "text-[var(--color-primary)] font-bold"
                                                        : "text-[var(--color-text)]"
                                                    }`}
                                            >
                                                <span
                                                    className="w-2.5 h-2.5 rounded-full shrink-0"
                                                    style={{ backgroundColor: t.accent }}
                                                />
                                                <span className="flex-1">{t.name}</span>
                                                {theme === t.id && (
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M20 6L9 17l-5-5" />
                                                    </svg>
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
