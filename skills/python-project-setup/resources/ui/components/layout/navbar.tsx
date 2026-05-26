"use client";

import { useSidebar } from "@/hooks/use-sidebar";

interface NavbarProps {
    /** Page title shown in the navbar */
    title?: string;
    /** Page description shown below title */
    description?: string;
    /** Optional action buttons (right side, before icons) */
    actions?: React.ReactNode;
}

/**
 * Navbar — Top navigation bar.
 *
 * Layout: [☰] [Title/Desc]  ...  [actions] [🔍] [U]
 *
 * Theme switcher moved to Settings panel (sidebar footer).
 * Notifications handled via toast system (BEW pattern).
 */
export function Navbar({ title, description, actions }: NavbarProps) {
    const { toggle } = useSidebar();

    return (
        <header className="flex items-center h-14 px-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] shrink-0">
            {/* Left: Mobile menu + Page info */}
            <div className="flex items-center gap-3 min-w-0 flex-1">
                <button
                    onClick={toggle}
                    className="lg:hidden w-8 h-8 flex items-center justify-center rounded-md hover:bg-[var(--color-primary-light)] text-[var(--color-text-muted)] transition-colors shrink-0"
                    aria-label="Toggle sidebar"
                >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <path d="M3 6h18M3 12h18M3 18h18" />
                    </svg>
                </button>

                {title && (
                    <div className="min-w-0">
                        <h1 className="text-base font-semibold text-[var(--color-text)] truncate leading-tight">
                            {title}
                        </h1>
                        {description && (
                            <p className="text-xs text-[var(--color-text-muted)] truncate leading-tight">
                                {description}
                            </p>
                        )}
                    </div>
                )}
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-1.5 shrink-0">
                {/* Page-specific actions */}
                {actions}

                {/* Search */}
                <button
                    className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-[var(--color-primary-light)] text-[var(--color-text-muted)] transition-colors"
                    title="Search (Ctrl+K)"
                    aria-label="Search"
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <circle cx="11" cy="11" r="8" />
                        <path d="M21 21l-4.35-4.35" />
                    </svg>
                </button>

                {/* User avatar */}
                <button
                    className="w-8 h-8 rounded-full bg-[var(--color-primary)] flex items-center justify-center text-[var(--color-primary-foreground)] text-xs font-bold transition-opacity hover:opacity-80 ml-1"
                    title="Account"
                    aria-label="Account menu"
                >
                    U
                </button>
            </div>
        </header>
    );
}
