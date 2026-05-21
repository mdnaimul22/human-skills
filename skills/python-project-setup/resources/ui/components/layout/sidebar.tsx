"use client";

import { useSidebar } from "@/hooks/use-sidebar";
import { ThemeSwitcher } from "./theme-switcher";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

/** Navigation item definition — config-driven, easy to extend */
interface NavItem {
    label: string;
    href: string;
    icon: string;
}

const NAV_ITEMS: NavItem[] = [
    { label: "Dashboard", href: "/",         icon: "📊" },
    { label: "Users",     href: "/users",    icon: "👥" },
    { label: "Settings",  href: "/settings", icon: "⚙️" },
];

/**
 * Sidebar Component
 *
 * Features:
 * - Collapsible on desktop (280px ↔ 64px icon-rail)
 * - Drawer overlay on mobile
 * - Active link highlighting
 * - Theme switcher at bottom
 * - Close on route change (mobile)
 * - Close on outside click (mobile)
 * - Keyboard accessible (Escape to close)
 */
export function Sidebar() {
    const { isOpen, isCollapsed, close, toggleCollapse } = useSidebar();
    const pathname = usePathname();

    // Close mobile sidebar on route change
    useEffect(() => {
        close();
    }, [pathname, close]);

    // Close on Escape key
    useEffect(() => {
        function handleKey(e: KeyboardEvent) {
            if (e.key === "Escape") close();
        }
        document.addEventListener("keydown", handleKey);
        return () => document.removeEventListener("keydown", handleKey);
    }, [close]);

    return (
        <>
            {/* Mobile overlay backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
                    onClick={close}
                    aria-hidden="true"
                />
            )}

            {/* Sidebar panel */}
            <aside
                className={`
                    fixed lg:relative inset-y-0 left-0 z-50
                    flex flex-col
                    bg-[var(--color-surface)] border-r border-[var(--color-border)]
                    transition-all duration-300 ease-in-out
                    ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
                    ${isCollapsed ? "lg:w-[var(--sidebar-collapsed-width)]" : "lg:w-[var(--sidebar-width)]"}
                    w-[var(--sidebar-width)]
                `}
                role="navigation"
                aria-label="Main navigation"
            >
                {/* Header */}
                <div className="flex items-center justify-between h-16 px-4 border-b border-[var(--color-border)]">
                    {!isCollapsed && (
                        <span className="text-lg font-bold text-[var(--color-text)] truncate">
                            ⚡ App
                        </span>
                    )}
                    <button
                        onClick={toggleCollapse}
                        className="hidden lg:flex w-8 h-8 items-center justify-center rounded-md hover:bg-[var(--color-primary-light)] text-[var(--color-text-muted)] transition-colors"
                        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {isCollapsed ? "→" : "←"}
                    </button>
                </div>

                {/* Navigation links */}
                <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
                    {NAV_ITEMS.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`
                                    flex items-center gap-3 px-3 py-2.5 rounded-lg
                                    transition-colors text-sm font-medium
                                    ${isActive
                                        ? "bg-[var(--color-primary-light)] text-[var(--color-primary)]"
                                        : "text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-primary-light)]"
                                    }
                                `}
                                title={isCollapsed ? item.label : undefined}
                            >
                                <span className="text-base shrink-0">{item.icon}</span>
                                {!isCollapsed && <span className="truncate">{item.label}</span>}
                            </Link>
                        );
                    })}
                </nav>

                {/* Bottom section: Theme Switcher */}
                <div className="p-3 border-t border-[var(--color-border)]">
                    {!isCollapsed && <ThemeSwitcher />}
                    {isCollapsed && (
                        <button
                            className="w-full flex items-center justify-center h-9 rounded-lg hover:bg-[var(--color-primary-light)] text-[var(--color-text-muted)] transition-colors"
                            title="Theme"
                        >
                            🎨
                        </button>
                    )}
                </div>
            </aside>
        </>
    );
}
