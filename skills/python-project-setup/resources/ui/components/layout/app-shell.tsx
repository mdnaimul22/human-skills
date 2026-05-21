"use client";

import { Sidebar } from "./sidebar";
import { Navbar } from "./navbar";

/**
 * AppShell — Root layout wrapper.
 * Composes Sidebar + Navbar + scrollable Content area.
 *
 * Layout:
 * ┌──────────┬───────────────────────────┐
 * │          │  Navbar                   │
 * │ Sidebar  ├───────────────────────────┤
 * │          │  Content (scrollable)     │
 * │          │                           │
 * └──────────┴───────────────────────────┘
 */
export function AppShell({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex h-screen overflow-hidden bg-[var(--color-bg)]">
            <Sidebar />
            <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
                <Navbar />
                <main className="flex-1 overflow-y-auto p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}
