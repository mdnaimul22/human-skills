"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SidebarState {
    /** Whether the sidebar is open (visible) on mobile */
    isOpen: boolean;
    /** Whether the sidebar is collapsed to icon-rail on desktop */
    isCollapsed: boolean;
    /** Custom width set by drag-resize (null = use CSS default) */
    customWidth: number | null;
    /** Toggle sidebar open/close (mobile) */
    toggle: () => void;
    /** Open sidebar (mobile) */
    open: () => void;
    /** Close sidebar (mobile) */
    close: () => void;
    /** Toggle collapse state (desktop) */
    toggleCollapse: () => void;
    /** Set collapsed state explicitly */
    setCollapsed: (collapsed: boolean) => void;
    /** Set custom drag-resize width */
    setCustomWidth: (w: number | null) => void;
}

/**
 * Zustand store for sidebar state.
 * Persisted to localStorage so collapse preference survives page reload.
 */
export const useSidebar = create<SidebarState>()(
    persist(
        (set) => ({
            isOpen: false,
            isCollapsed: false,
            customWidth: null,
            toggle: () => set((s) => ({ isOpen: !s.isOpen })),
            open: () => set({ isOpen: true }),
            close: () => set({ isOpen: false }),
            toggleCollapse: () => set((s) => ({
                isCollapsed: !s.isCollapsed,
                // Clear custom width when toggling collapse so CSS takes over
                customWidth: null,
            })),
            setCollapsed: (collapsed: boolean) => set({
                isCollapsed: collapsed,
                customWidth: null,
            }),
            setCustomWidth: (w: number | null) => set({ customWidth: w }),
        }),
        {
            name: "sidebar-state",
            partialize: (state) => ({
                isCollapsed: state.isCollapsed,
                customWidth: state.customWidth,
            }),
        },
    ),
);
