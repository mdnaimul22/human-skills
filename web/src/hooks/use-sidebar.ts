"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SidebarState {
    /** Whether the sidebar is open (visible) on mobile */
    isOpen: boolean;
    /** Whether the sidebar is collapsed to icon-rail on desktop */
    isCollapsed: boolean;
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
            toggle: () => set((s) => ({ isOpen: !s.isOpen })),
            open: () => set({ isOpen: true }),
            close: () => set({ isOpen: false }),
            toggleCollapse: () => set((s) => ({ isCollapsed: !s.isCollapsed })),
            setCollapsed: (collapsed: boolean) => set({ isCollapsed: collapsed }),
        }),
        {
            name: "sidebar-state",
            partialize: (state) => ({ isCollapsed: state.isCollapsed }),
        },
    ),
);
