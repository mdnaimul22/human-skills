"use client";

import { Sidebar } from "./sidebar";
import { Navbar } from "./navbar";

interface AppShellProps {
    children: React.ReactNode;
    /** Page title shown in navbar */
    title?: string;
    /** Page description shown in navbar */
    description?: string;
    /** Action buttons shown in navbar (right side) */
    actions?: React.ReactNode;
}

/**
 * AppShell — Root layout wrapper.
 * Composes Sidebar + Navbar + scrollable Content area.
 *
 * Layout:
 * ┌──────────┬───────────────────────────┐
 * │          │  Navbar [Title] [Actions] │
 * │ Sidebar  ├───────────────────────────┤
 * │          │  Content (scrollable)     │
 * └──────────┴───────────────────────────┘
 */
export function AppShell({ children, title, description, actions }: AppShellProps) {
    return (
        <div className="flex h-screen overflow-hidden bg-[var(--color-bg)]">
            <Sidebar />
            <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
                <Navbar title={title} description={description} actions={actions} />
                <main className="flex-1 overflow-y-auto p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}
