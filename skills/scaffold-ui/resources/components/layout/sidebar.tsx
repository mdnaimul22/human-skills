"use client";

import { useSidebar } from "@/hooks/use-sidebar";
import { SettingsPanel } from "./settings";
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
    { label: "Dashboard", href: "/", icon: "📊" },
];

const MIN_WIDTH = 180;
const MAX_WIDTH = 400;

/**
 * Sidebar Component
 *
 * Features:
 * - Drag-to-resize via right border handle
 * - Collapsible on desktop (icon-rail mode)
 * - Drawer overlay on mobile
 * - Active link highlighting
 * - Close on route change (mobile)
 * - Keyboard accessible (Escape to close)
 */
export function Sidebar() {
    const { isOpen, isCollapsed, close, toggleCollapse, setCollapsed, customWidth, setCustomWidth } = useSidebar();
    const pathname = usePathname();
    const sidebarRef = useRef<HTMLElement>(null);
    const isResizing = useRef(false);
    const lastWidth = useRef<number>(0);

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
            lastWidth.current = 0;
            document.body.style.cursor = "col-resize";
            document.body.style.userSelect = "none";

            function onMouseMove(ev: MouseEvent) {
                if (!isResizing.current || !sidebarRef.current) return;
                const newWidth = ev.clientX;

                if (newWidth < MIN_WIDTH / 2) {
                    setCollapsed(true);
                    sidebarRef.current.style.width = "";
                    lastWidth.current = 0;
                } else {
                    setCollapsed(false);
                    const clamped = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, newWidth));
                    sidebarRef.current.style.width = `${clamped}px`;
                    lastWidth.current = clamped;
                }
            }

            function onMouseUp() {
                isResizing.current = false;
                document.body.style.cursor = "";
                document.body.style.userSelect = "";
                // Persist the final dragged width to store (survives re-renders)
                if (lastWidth.current > 0) {
                    setCustomWidth(lastWidth.current);
                }
                // Clear inline style — width is now driven by store via style prop
                if (sidebarRef.current) {
                    sidebarRef.current.style.width = "";
                }
                document.removeEventListener("mousemove", onMouseMove);
                document.removeEventListener("mouseup", onMouseUp);
            }

            document.addEventListener("mousemove", onMouseMove);
            document.addEventListener("mouseup", onMouseUp);
        },
        [setCollapsed, setCustomWidth],
    );

    // Compute sidebar width style
    const sidebarStyle: React.CSSProperties | undefined =
        !isCollapsed && customWidth ? { width: `${customWidth}px` } : undefined;

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
                style={sidebarStyle}
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
                <div className="flex items-center h-14 px-3 border-b border-[var(--color-border)]">
                    {!isCollapsed && (
                        <span className="text-base font-bold text-[var(--color-text)] truncate pl-1 flex-1">
                            ⚡ App
                        </span>
                    )}
                    <button
                        onClick={toggleCollapse}
                        className="hidden lg:flex w-9 h-9 items-center justify-center rounded-md border border-transparent hover:border-[var(--color-border)] hover:bg-[var(--color-primary-light)] text-[var(--color-text-secondary)] transition-all"
                        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {isCollapsed ? (
                            /* >> expand icon */
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M13 5l7 7-7 7" />
                                <path d="M4 5l7 7-7 7" />
                            </svg>
                        ) : (
                            /* << collapse icon */
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M11 19l-7-7 7-7" />
                                <path d="M20 19l-7-7 7-7" />
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

                {/* Sidebar Footer — Settings */}
                <div className="p-2 border-t border-[var(--color-border)]">
                    <SettingsPanel collapsed={isCollapsed} />
                </div>

                {/* ── Resize handle (right border) ────────────── */}
                {/* 8px invisible hit area — visible bar shows on hover with smooth fade */}
                <div
                    onMouseDown={handleMouseDown}
                    className="
                        hidden lg:block
                        absolute top-0 h-full
                        cursor-col-resize group
                        z-[60]
                    "
                    style={{
                        right: "-4px",
                        width: "8px",
                    }}
                    title="Drag to resize"
                >
                    {/* Visible 2px bar — centered within hit area, smooth fade */}
                    <div
                        className="
                            absolute top-0 left-1/2 -translate-x-1/2
                            w-[2px] h-full rounded-full
                            bg-[var(--color-primary)]
                            opacity-0 group-hover:opacity-50 group-active:opacity-70
                            transition-opacity duration-300 ease-out
                        "
                    />
                </div>
            </aside>
        </>
    );
}
