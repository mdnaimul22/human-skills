"use client";

import { useSidebar } from "@/hooks/use-sidebar";

/**
 * Navbar Component — Top navigation bar.
 *
 * Features:
 * - Hamburger menu (mobile sidebar toggle)
 * - Search placeholder
 * - Notification bell
 * - User avatar
 */
export function Navbar() {
    const { toggle } = useSidebar();

    return (
        <header className="flex items-center justify-between h-16 px-6 border-b border-[var(--color-border)] bg-[var(--color-bg)]">
            {/* Left: Mobile menu + Breadcrumb area */}
            <div className="flex items-center gap-4">
                <button
                    onClick={toggle}
                    className="lg:hidden w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[var(--color-primary-light)] text-[var(--color-text-muted)] transition-colors"
                    aria-label="Toggle sidebar"
                >
                    ☰
                </button>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-3">
                {/* Search */}
                <button
                    className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[var(--color-primary-light)] text-[var(--color-text-muted)] transition-colors"
                    title="Search (Ctrl+K)"
                    aria-label="Search"
                >
                    🔍
                </button>

                {/* Notifications */}
                <button
                    className="relative w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[var(--color-primary-light)] text-[var(--color-text-muted)] transition-colors"
                    title="Notifications"
                    aria-label="Notifications"
                >
                    🔔
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[var(--color-danger)]" />
                </button>

                {/* User avatar */}
                <button
                    className="w-9 h-9 rounded-full bg-[var(--color-primary)] flex items-center justify-center text-[var(--color-primary-foreground)] text-sm font-bold transition-opacity hover:opacity-80"
                    title="Account"
                    aria-label="Account menu"
                >
                    U
                </button>
            </div>
        </header>
    );
}
