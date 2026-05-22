"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

/** Theme metadata for the selector UI */
interface ThemeMeta {
    id: string;
    name: string;
    accent: string;
    type: "dark" | "light";
}

const THEMES: ThemeMeta[] = [
    { id: "dark",        name: "Default",   accent: "#3b82f6", type: "dark" },
    { id: "matrix",      name: "Matrix",    accent: "#10b981", type: "dark" },
    { id: "cream",       name: "Monokai",   accent: "#a6e22e", type: "dark" },
    { id: "matte-black", name: "VS Code",   accent: "#007acc", type: "dark" },
    { id: "black-brown", name: "Dracula",   accent: "#bd93f9", type: "dark" },
    { id: "jam-black",   name: "One Dark",  accent: "#61afef", type: "dark" },
    { id: "jam-navy",    name: "Nord",      accent: "#88c0d0", type: "dark" },
    { id: "light",       name: "Clear Ice", accent: "#1d4ed8", type: "light" },
    { id: "snow",        name: "Snow",      accent: "#3b82f6", type: "light" },
];

interface ThemeSwitcherProps {
    /** When true, shows only a compact icon button */
    collapsed?: boolean;
}

/**
 * Theme Switcher Component (ChainCV dropdown pattern)
 *
 * Anti-flicker: renders nothing until mounted to prevent hydration mismatch.
 * Supports collapsed mode for sidebar icon-rail.
 */
export function ThemeSwitcher({ collapsed = false }: ThemeSwitcherProps) {
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);
    const [open, setOpen] = useState(false);

    // Prevent hydration mismatch — only render after client mount
    useEffect(() => setMounted(true), []);
    if (!mounted) return <ThemeSwitcherSkeleton collapsed={collapsed} />;

    const current = THEMES.find((t) => t.id === theme) ?? THEMES[0];

    /** Cycle to next theme on click */
    function cycleTheme() {
        const idx = THEMES.findIndex((t) => t.id === theme);
        const next = THEMES[(idx + 1) % THEMES.length];
        setTheme(next.id);
    }

    // ── Collapsed mode: icon-only button ──────────────────────
    if (collapsed) {
        return (
            <button
                onClick={cycleTheme}
                className="w-full flex items-center justify-center h-9 rounded-lg hover:bg-[var(--color-primary-light)] transition-colors"
                title={`Theme: ${current.name} — click to cycle`}
            >
                <span
                    className="w-3 h-3 rounded-full ring-2 ring-[var(--color-border)]"
                    style={{ backgroundColor: current.accent }}
                />
            </button>
        );
    }

    // ── Expanded mode: full dropdown ──────────────────────────
    return (
        <div className="relative" onMouseLeave={() => setOpen(false)}>
            {/* Active theme button */}
            <div className="flex items-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden h-9">
                <button
                    onClick={cycleTheme}
                    className="flex items-center gap-2 px-3 h-full flex-1 hover:bg-[var(--color-primary-light)] transition-colors"
                    title={`Theme: ${current.name} — click to cycle`}
                >
                    <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: current.accent }}
                    />
                    <span className="text-[11px] font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
                        {current.name}
                    </span>
                </button>

                <div className="w-px h-4 bg-[var(--color-border)]" />

                <button
                    onClick={() => setOpen(!open)}
                    className="px-2 h-full hover:bg-[var(--color-primary-light)] text-[10px] text-[var(--color-text-muted)] transition-colors"
                    aria-label="Open theme list"
                >
                    ▾
                </button>
            </div>

            {/* Dropdown */}
            {open && (
                <div className="absolute bottom-full left-0 mb-2 w-48 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] shadow-lg p-1 z-50 animate-in fade-in slide-in-from-bottom-2 duration-200">
                    {THEMES.map((t) => (
                        <button
                            key={t.id}
                            onClick={() => {
                                setTheme(t.id);
                                setOpen(false);
                            }}
                            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                                theme === t.id
                                    ? "bg-[var(--color-primary-light)]"
                                    : "hover:bg-[var(--color-primary-light)]"
                            }`}
                        >
                            <span
                                className="w-2.5 h-2.5 rounded-full shrink-0"
                                style={{ backgroundColor: t.accent }}
                            />
                            <span
                                className={`text-[11px] font-medium flex-1 ${
                                    theme === t.id
                                        ? "text-[var(--color-primary)]"
                                        : "text-[var(--color-text-secondary)]"
                                }`}
                            >
                                {t.name}
                            </span>
                            <span className="text-[10px] opacity-50">
                                {t.type === "light" ? "☀️" : "🌙"}
                            </span>
                            {theme === t.id && (
                                <span className="text-[var(--color-primary)] text-xs">✓</span>
                            )}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

/** Skeleton placeholder to avoid layout shift before mount */
function ThemeSwitcherSkeleton({ collapsed }: { collapsed?: boolean }) {
    if (collapsed) {
        return <div className="h-9 w-9 mx-auto rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] animate-pulse" />;
    }
    return (
        <div className="h-9 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] animate-pulse" />
    );
}
