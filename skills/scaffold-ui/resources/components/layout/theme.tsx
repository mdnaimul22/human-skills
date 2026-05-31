"use client";

import { useTheme } from "next-themes";
import { useEffect, useRef, useState } from "react";

/* ═══════════════════════════════════════════════════════════════
   ThemeLoadedScript
   
   Adds `theme-loaded` class to body after first paint.
   This enables smooth background-color transitions AFTER
   the initial theme is resolved — preventing flicker.
   ═══════════════════════════════════════════════════════════════ */

export function ThemeLoadedScript() {
    useEffect(() => {
        requestAnimationFrame(() => {
            document.body.classList.add("theme-loaded");
        });
    }, []);

    return null;
}

/* ═══════════════════════════════════════════════════════════════
   ThemeSwitcher — Navbar icon button with dropdown.

   Renders a small accent-color dot that opens a full theme list
   on click. Anti-flicker: skeleton until client mount.
   ═══════════════════════════════════════════════════════════════ */

/** Theme metadata for the selector UI */
interface ThemeMeta {
    id: string;
    name: string;
    accent: string;
    type: "dark" | "light";
}

const THEMES: ThemeMeta[] = [
    { id: "dark", name: "Default", accent: "#3b82f6", type: "dark" },
    { id: "matrix", name: "Matrix", accent: "#10b981", type: "dark" },
    { id: "cream", name: "Monokai", accent: "#a6e22e", type: "dark" },
    { id: "matte-black", name: "VS Code", accent: "#007acc", type: "dark" },
    { id: "black-brown", name: "Dracula", accent: "#bd93f9", type: "dark" },
    { id: "jam-black", name: "One Dark", accent: "#61afef", type: "dark" },
    { id: "jam-navy", name: "Nord", accent: "#88c0d0", type: "dark" },
    { id: "light", name: "Clear Ice", accent: "#1d4ed8", type: "light" },
    { id: "snow", name: "Snow", accent: "#3b82f6", type: "light" },
];

export function ThemeSwitcher() {
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => setMounted(true), []);

    // Close on outside click
    useEffect(() => {
        if (!open) return;
        function handler(e: MouseEvent) {
            if (ref.current && !ref.current.contains(e.target as Node)) {
                setOpen(false);
            }
        }
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, [open]);

    if (!mounted) {
        return (
            <div className="w-8 h-8 rounded-md bg-[var(--color-surface)] animate-pulse" />
        );
    }

    const current = THEMES.find((t) => t.id === theme) ?? THEMES[0];

    return (
        <div className="relative" ref={ref}>
            {/* Trigger button */}
            <button
                onClick={() => setOpen(!open)}
                className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-[var(--color-primary-light)] transition-colors"
                title={`Theme: ${current.name}`}
                aria-label="Change theme"
            >
                <span
                    className="w-3.5 h-3.5 rounded-full ring-2 ring-[var(--color-border)]"
                    style={{ backgroundColor: current.accent }}
                />
            </button>

            {/* Dropdown */}
            {open && (
                <div className="absolute top-full right-0 mt-2 w-48 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] shadow-lg p-1 z-[100]">
                    <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                        Theme
                    </div>
                    {THEMES.map((t) => (
                        <button
                            key={t.id}
                            onClick={() => {
                                setTheme(t.id);
                                setOpen(false);
                            }}
                            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-colors ${theme === t.id
                                    ? "bg-[var(--color-primary-light)]"
                                    : "hover:bg-[var(--color-primary-light)]"
                                }`}
                        >
                            <span
                                className="w-2.5 h-2.5 rounded-full shrink-0"
                                style={{ backgroundColor: t.accent }}
                            />
                            <span
                                className={`text-xs font-medium flex-1 ${theme === t.id
                                        ? "text-[var(--color-primary)]"
                                        : "text-[var(--color-text-secondary)]"
                                    }`}
                            >
                                {t.name}
                            </span>
                            <span className="text-[10px] opacity-40">
                                {t.type === "light" ? "☀" : "🌙"}
                            </span>
                            {theme === t.id && (
                                <span className="text-[var(--color-primary)] text-xs font-bold">✓</span>
                            )}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
