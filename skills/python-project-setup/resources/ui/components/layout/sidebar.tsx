"use client";

import { useSidebar } from "@/hooks/use-sidebar";
import { ThemeSwitcher } from "./theme-switcher";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useCallback, useRef } from "react";

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

const MIN_WIDTH = 200;
const MAX_WIDTH = 400;

/**
 * Sidebar Component
 *
 * Features:
 * - Drag-to-resize via right border handle
 * - Collapsible on desktop (icon-rail mode)
 * - Drawer overlay on mobile
 * - Active link highlighting
 * - Theme switcher at bottom (always visible)
 * - Close on route change (mobile)
 * - Keyboard accessible (Escape to close)
 */
export function Sidebar() {
    const { isOpen, isCollapsed, close, toggleCollapse, setCollapsed } = useSidebar();
    const pathname = usePathname();
    const sidebarRef = useRef<HTMLElement>(null);
    const isResizing = useRef(false);

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

    // ── Drag-to-resize logic ──────────────────────────────────
    const handleMouseDown = useCallback(
        (e: React.MouseEvent) => {
            e.preventDefault();
            isResizing.current = true;
            document.body.style.cursor = "col-resize";
            document.body.style.userSelect = "none";

            function onMouseMove(ev: MouseEvent) {
                if (!isResizing.current || !sidebarRef.current) return;
                const newWidth = ev.clientX;

                if (newWidth < MIN_WIDTH / 2) {
                    // Snap to collapsed
                    setCollapsed(true);
                    sidebarRef.current.style.width = "";
                } else {
                    setCollapsed(false);
                    const clamped = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, newWidth));
                    sidebarRef.current.style.width = `${clamped}px`;
                }
            }

            function onMouseUp() {
                isResizing.current = false;
                document.body.style.cursor = "";
                document.body.style.userSelect = "";
                document.removeEventListener("mousemove", onMouseMove);
                document.removeEventListener("mouseup", onMouseUp);
            }

            document.addEventListener("mousemove", onMouseMove);
            document.addEventListener("mouseup", onMouseUp);
        },
        [setCollapsed],
    );

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
                ref={sidebarRef}
                className={`
                    fixed lg:relative inset-y-0 left-0 z-50
                    flex flex-col
                    bg-[var(--color-surface)]
                    transition-all duration-300 ease-in-out
                    ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
                    ${isCollapsed ? "lg:w-16" : "lg:w-[var(--sidebar-width)]"}
                    w-[var(--sidebar-width)]
                `}
                role="navigation"
                aria-label="Main navigation"
            >
                {/* Header */}
                <div className="flex items-center justify-between h-14 px-3 border-b border-[var(--color-border)]">
                    {!isCollapsed && (
                        <span className="text-base font-bold text-[var(--color-text)] truncate pl-1">
                            ⚡ App
                        </span>
                    )}
                    <button
                        onClick={toggleCollapse}
                        className="hidden lg:flex w-8 h-8 items-center justify-center rounded-md hover:bg-[var(--color-primary-light)] text-[var(--color-text-muted)] transition-colors ml-auto"
                        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {/* Chevron SVG icons */}
                        {isCollapsed ? (
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M6 3l5 5-5 5" />
                            </svg>
                        ) : (
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M10 3L5 8l5 5" />
                            </svg>
                        )}
                    </button>
                </div>

                {/* Navigation links */}
                <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
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
                                    ${isCollapsed ? "justify-center px-0" : ""}
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
                <div className="p-2 border-t border-[var(--color-border)]">
                    <ThemeSwitcher collapsed={isCollapsed} />
                </div>

                {/* ── Resize handle (right border) ────────────── */}
                <div
                    onMouseDown={handleMouseDown}
                    className="
                        hidden lg:block
                        absolute top-0 right-0 w-1 h-full
                        cursor-col-resize
                        hover:bg-[var(--color-primary)] hover:opacity-60
                        active:bg-[var(--color-primary)] active:opacity-80
                        transition-colors duration-150
                        z-[60]
                    "
                    title="Drag to resize"
                />
            </aside>
        </>
    );
}
