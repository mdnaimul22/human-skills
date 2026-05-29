"use client";

import { create } from "zustand";
import { useEffect, useState } from "react";

/* ── Toast types & store ─────────────────────────────────── */

type ToastType = "success" | "error" | "info";

interface Toast {
    id: string;
    message: string;
    type: ToastType;
}

interface ToastStore {
    toasts: Toast[];
    add: (message: string, type?: ToastType) => void;
    remove: (id: string) => void;
}

export const useToast = create<ToastStore>((set) => ({
    toasts: [],
    add: (message, type = "info") =>
        set((s) => ({
            toasts: [
                ...s.toasts,
                { id: `${Date.now()}-${Math.random()}`, message, type },
            ],
        })),
    remove: (id) =>
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

/* ── Individual toast item ───────────────────────────────── */

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        // Animate in
        requestAnimationFrame(() => setVisible(true));
        // Auto-dismiss after 5s
        const timer = setTimeout(() => setVisible(false), 5000);
        return () => clearTimeout(timer);
    }, []);

    // Remove from DOM after fade-out
    useEffect(() => {
        if (!visible) {
            const cleanup = setTimeout(onRemove, 300);
            return () => clearTimeout(cleanup);
        }
    }, [visible, onRemove]);

    const colors: Record<ToastType, { bg: string; border: string; icon: string }> = {
        success: {
            bg: "var(--color-success, #10b981)",
            border: "var(--color-success, #10b981)",
            icon: "M20 6L9 17l-5-5",
        },
        error: {
            bg: "var(--color-danger, #ef4444)",
            border: "var(--color-danger, #ef4444)",
            icon: "M18 6L6 18M6 6l12 12",
        },
        info: {
            bg: "var(--color-primary, #3b82f6)",
            border: "var(--color-primary-dark, #2563eb)",
            icon: "M12 8v4m0 4h.01M12 2a10 10 0 100 20 10 10 0 000-20z",
        },
    };

    const c = colors[toast.type];

    return (
        <div
            role="alert"
            className="flex items-center gap-3 text-sm shadow-lg rounded-lg px-4 py-2.5 text-white transition-all duration-300 ease-out"
            style={{
                backgroundColor: c.bg,
                borderLeft: `3px solid ${c.border}`,
                opacity: visible ? 1 : 0,
                transform: visible ? "translateY(0)" : "translateY(8px)",
            }}
        >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                <path d={c.icon} />
            </svg>
            <span className="flex-1">{toast.message}</span>
            <button
                onClick={() => setVisible(false)}
                className="text-white/70 hover:text-white ml-2 text-base leading-none"
            >
                &times;
            </button>
        </div>
    );
}

/* ── Toast container (mount once in layout) ──────────────── */

export function ToastContainer() {
    const { toasts, remove } = useToast();

    if (toasts.length === 0) return null;

    return (
        <div
            className="fixed bottom-4 right-4 z-[2000] w-full max-w-sm space-y-2"
            aria-live="polite"
        >
            {toasts.map((t) => (
                <ToastItem key={t.id} toast={t} onRemove={() => remove(t.id)} />
            ))}
        </div>
    );
}
