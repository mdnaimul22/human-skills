"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import { LoginModal } from "./login-modal";
import {
    DropdownMenu,
    DropdownMenuTrigger,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuGroup,
    DropdownMenuLabel,
    DropdownMenuSub,
    DropdownMenuSubTrigger,
    DropdownMenuSubContent,
} from "@/components/ui/dropdown-menu";

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
    { key: "outfit", label: "Outfit", family: "var(--font-outfit), system-ui, sans-serif" },
    { key: "space-grotesk", label: "Space Grotesk", family: "var(--font-space-grotesk), system-ui, sans-serif" },
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
    { id: "claude", name: "Warm Light", accent: "#d97706" },
    { id: "custom", name: "Cinematic", accent: "#dc2626" },
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
            version: 1,
            migrate: () => ({ fontKey: "system", scaleKey: "m", setFont: () => {}, setScale: () => {} }),
        },
    ),
);

/* ── Side-effect: apply font + scale to <html> ───────────── */

const DEFAULT_FONT_KEY = "system";
const DEFAULT_SCALE_KEY = "m";

export function useApplySettings() {
    const { fontKey, scaleKey } = useAppSettings();

    useEffect(() => {
        const html = document.documentElement;

        // Font: set both --font-primary and --font-sans to apply globally
        if (fontKey !== DEFAULT_FONT_KEY) {
            const font = FONTS.find((f) => f.key === fontKey) ?? FONTS[0];
            html.style.setProperty("--font-primary", font.family);
            html.style.setProperty("--font-sans", font.family);
        } else {
            html.style.removeProperty("--font-primary");
            html.style.removeProperty("--font-sans");
        }

        // Scale: only set fontSize when not using default (16px)
        if (scaleKey !== DEFAULT_SCALE_KEY) {
            const scale = SCALES.find((s) => s.key === scaleKey) ?? SCALES[1];
            html.style.fontSize = scale.size;
        } else {
            html.style.removeProperty("font-size");
        }

        // Clean up empty style attribute to avoid DOM mutation noise
        if (!html.getAttribute("style")?.trim()) {
            html.removeAttribute("style");
        }
    }, [fontKey, scaleKey]);
}

/* ── UserMenu Component ────────────────────────────── */

interface UserMenuProps {
    collapsed?: boolean;
}

export function UserMenu({ collapsed = false }: UserMenuProps) {
    const { fontKey, scaleKey, setFont, setScale } = useAppSettings();
    const { theme, setTheme } = useTheme();
    const { isAuthenticated, user, logout } = useAuth();
    const [mounted, setMounted] = useState(false);
    
    const [loginOpen, setLoginOpen] = useState(false);

    useEffect(() => setMounted(true), []);

    // Apply settings to DOM
    useApplySettings();

    const currentFont = FONTS.find((f) => f.key === fontKey) ?? FONTS[0];
    const currentTheme = mounted
        ? (THEMES.find((t) => t.id === theme) ?? THEMES[0])
        : THEMES[0];

    const userInitial = user?.name?.[0]?.toUpperCase() || "U";
    const userEmail = user?.email || "User";
    const userName = user?.name || "User";

    return (
        <>
            <DropdownMenu>
                <DropdownMenuTrigger className={`
                    w-full flex items-center gap-3 rounded-lg transition-all overflow-hidden
                    text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-primary-light)]
                    focus:outline-none cursor-pointer
                    ${collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2.5"}
                `}>
                    <div className="w-8 h-8 rounded-full bg-[var(--color-primary)] shrink-0 flex items-center justify-center text-[var(--color-primary-foreground)] text-sm font-bold">
                        {isAuthenticated ? userInitial : (
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                        )}
                    </div>
                    {!collapsed && (
                        <div className="flex flex-col items-start min-w-0 flex-1">
                            <span className="text-sm font-medium truncate w-full text-left">
                                {isAuthenticated ? userName : "Guest"}
                            </span>
                            <span className="text-xs text-[var(--color-text-muted)] truncate w-full text-left">
                                {isAuthenticated ? "Settings & Profile" : "Login to save data"}
                            </span>
                        </div>
                    )}
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" sideOffset={8} className="w-64 z-[100]">
                    {isAuthenticated ? (
                        <div className="px-2 py-1.5 flex flex-col">
                            <span className="text-sm font-medium text-[var(--color-text)] truncate">{userName}</span>
                            <span className="text-xs text-[var(--color-text-muted)] truncate">{userEmail}</span>
                        </div>
                    ) : (
                        <div className="px-2 py-1.5 flex flex-col">
                            <span className="text-sm font-medium text-[var(--color-text)]">Guest Session</span>
                        </div>
                    )}
                    
                    <DropdownMenuSeparator />
                    
                    <DropdownMenuGroup>
                        <DropdownMenuLabel>Settings</DropdownMenuLabel>
                        
                        {/* Theme Row (Click label/pill to cycle, click arrow for dropdown) */}
                        <div className="flex items-center justify-between px-2.5 py-1.5 text-sm hover:bg-[var(--color-primary-light)] transition-colors select-none rounded-md">
                            {/* Left part: click to cycle */}
                            <button
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    const idx = THEMES.findIndex((t) => t.id === theme);
                                    setTheme(THEMES[(idx + 1) % THEMES.length].id);
                                }}
                                className="flex items-center gap-2 text-[var(--color-text)] flex-1 text-left cursor-pointer outline-none py-1"
                            >
                                <svg className="w-4 h-4 text-[var(--color-text-secondary)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <circle cx="12" cy="12" r="5" />
                                    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                                </svg>
                                <span className="text-sm font-medium">Theme</span>
                            </button>
                            
                            {/* Right part: Split Button containing Pill (click to cycle) + Chevron (click for sub) */}
                            <div className="flex items-center gap-0">
                                <button
                                    onClick={(e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        const idx = THEMES.findIndex((t) => t.id === theme);
                                        setTheme(THEMES[(idx + 1) % THEMES.length].id);
                                    }}
                                    className="flex items-center gap-1.5 bg-[var(--color-bg)] hover:bg-[var(--color-primary-light)] border border-r-0 border-[var(--color-border)] rounded-l-md rounded-r-none px-2.5 h-7 transition-colors text-xs text-[var(--color-text-secondary)] font-semibold select-none cursor-pointer outline-none"
                                >
                                    <span
                                        className="w-2.5 h-2.5 rounded-full ring-1 ring-[var(--color-border)]"
                                        style={{ backgroundColor: currentTheme.accent }}
                                    />
                                    <span>{currentTheme.name}</span>
                                </button>
                                
                                <DropdownMenuSub>
                                    <DropdownMenuSubTrigger
                                        className="bg-[var(--color-bg)] hover:bg-[var(--color-primary-light)] border border-[var(--color-border)] rounded-r-md rounded-l-none px-2 h-7 transition-colors cursor-pointer text-[var(--color-text-muted)] flex items-center justify-center focus:outline-none data-open:bg-[var(--color-primary-light)]"
                                        delay={100}
                                        closeDelay={500}
                                        onPointerDown={(e) => e.stopPropagation()}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                    <DropdownMenuSubContent className="max-h-72 overflow-y-auto">
                                        {THEMES.map((t) => (
                                            <DropdownMenuItem 
                                                key={t.id} 
                                                onClick={() => setTheme(t.id)}
                                                className="flex items-center gap-2"
                                            >
                                                <span
                                                    className="w-2.5 h-2.5 rounded-full shrink-0"
                                                    style={{ backgroundColor: t.accent }}
                                                />
                                                <span className="flex-1">{t.name}</span>
                                                {mounted && theme === t.id && (
                                                    <svg className="w-4 h-4 ml-auto text-[var(--color-primary)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M20 6L9 17l-5-5" />
                                                    </svg>
                                                )}
                                            </DropdownMenuItem>
                                        ))}
                                    </DropdownMenuSubContent>
                                </DropdownMenuSub>
                            </div>
                        </div>

                        {/* Font Family Row (Click label/pill to cycle, click arrow for dropdown) */}
                        <div className="flex items-center justify-between px-2.5 py-1.5 text-sm hover:bg-[var(--color-primary-light)] transition-colors select-none rounded-md">
                            {/* Left part: click to cycle */}
                            <button
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    const idx = FONTS.findIndex((f) => f.key === fontKey);
                                    setFont(FONTS[(idx + 1) % FONTS.length].key);
                                }}
                                className="flex items-center gap-2 text-[var(--color-text)] flex-1 text-left cursor-pointer outline-none py-1"
                            >
                                <svg className="w-4 h-4 text-[var(--color-text-secondary)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M4 21V3l8 9 8-9v18" />
                                </svg>
                                <span className="text-sm font-medium">Font Family</span>
                            </button>
                            
                            {/* Right part: Split Button containing Pill (click to cycle) + Chevron (click for sub) */}
                            <div className="flex items-center gap-0">
                                <button
                                    onClick={(e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        const idx = FONTS.findIndex((f) => f.key === fontKey);
                                        setFont(FONTS[(idx + 1) % FONTS.length].key);
                                    }}
                                    className="flex items-center bg-[var(--color-bg)] hover:bg-[var(--color-primary-light)] border border-r-0 border-[var(--color-border)] rounded-l-md rounded-r-none px-2.5 h-7 transition-colors text-xs text-[var(--color-text-secondary)] font-semibold select-none cursor-pointer outline-none"
                                    style={{ fontFamily: currentFont.family }}
                                >
                                    <span>{currentFont.label}</span>
                                </button>
                                
                                <DropdownMenuSub>
                                    <DropdownMenuSubTrigger
                                        className="bg-[var(--color-bg)] hover:bg-[var(--color-primary-light)] border border-[var(--color-border)] rounded-r-md rounded-l-none px-2 h-7 transition-colors cursor-pointer text-[var(--color-text-muted)] flex items-center justify-center focus:outline-none data-open:bg-[var(--color-primary-light)]"
                                        delay={100}
                                        closeDelay={500}
                                        onPointerDown={(e) => e.stopPropagation()}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                    <DropdownMenuSubContent>
                                        {FONTS.map((f) => (
                                            <DropdownMenuItem 
                                                key={f.key} 
                                                onClick={() => setFont(f.key)}
                                                style={{ fontFamily: f.family }}
                                                className="flex items-center justify-between"
                                            >
                                                <span className="flex-1">{f.label}</span>
                                                {fontKey === f.key && (
                                                    <svg className="w-4 h-4 text-[var(--color-primary)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M20 6L9 17l-5-5" />
                                                    </svg>
                                                )}
                                            </DropdownMenuItem>
                                        ))}
                                    </DropdownMenuSubContent>
                                </DropdownMenuSub>
                            </div>
                        </div>

                        {/* Interface Size (Segmented control next to it) */}
                        <div className="flex items-center justify-between px-2.5 py-1.5">
                            <div className="flex items-center gap-2">
                                <svg className="w-4 h-4 text-[var(--color-text-secondary)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                    <path d="M4 7V4h16v3" />
                                    <path d="M9 20h6" />
                                    <path d="M12 4v16" />
                                </svg>
                                <span className="text-sm font-medium text-[var(--color-text)]">Size</span>
                            </div>
                            <div className="flex items-center gap-0.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-md p-0.5">
                                {SCALES.map((s) => (
                                    <button
                                        key={s.key}
                                        onClick={(e) => {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            setScale(s.key);
                                        }}
                                        className={`text-[10px] uppercase px-2 py-1 rounded-md transition-all font-bold cursor-pointer ${
                                            scaleKey === s.key
                                                ? "bg-[var(--color-card)] shadow-sm text-[var(--color-primary)] border border-[var(--color-border)]"
                                                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text)]"
                                        }`}
                                    >
                                        {s.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </DropdownMenuGroup>

                    <DropdownMenuSeparator />

                    {isAuthenticated ? (
                        <DropdownMenuItem onClick={logout} className="text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10 cursor-pointer">
                            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                <polyline points="16 17 21 12 16 7" />
                                <line x1="21" y1="12" x2="9" y2="12" />
                            </svg>
                            Log out
                        </DropdownMenuItem>
                    ) : (
                        <DropdownMenuItem onClick={() => setLoginOpen(true)} className="cursor-pointer">
                            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                                <polyline points="10 17 15 12 10 7" />
                                <line x1="15" y1="12" x2="3" y2="12" />
                            </svg>
                            Log in
                        </DropdownMenuItem>
                    )}
                </DropdownMenuContent>
            </DropdownMenu>

            {/* Login Modal */}
            <LoginModal
                isOpen={loginOpen}
                onClose={() => setLoginOpen(false)}
                defaultMode="login"
            />
        </>
    );
}
