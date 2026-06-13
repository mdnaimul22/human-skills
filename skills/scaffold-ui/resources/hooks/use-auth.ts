"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

/* ── Types ───────────────────────────────────────────── */

interface User {
    id: string;
    email: string;
    name: string;
    created_at: string;
}

interface AuthState {
    token: string | null;
    user: User | null;
    isAuthenticated: boolean;

    setAuth: (token: string, user: User) => void;
    logout: () => void;
    updateUser: (patch: Partial<User>) => void;
}

/* ── Store ────────────────────────────────────────────── */

export const useAuth = create<AuthState>()(
    persist(
        (set) => ({
            token: null,
            user: null,
            isAuthenticated: false,

            setAuth: (token, user) =>
                set({ token, user, isAuthenticated: true }),

            logout: () =>
                set({ token: null, user: null, isAuthenticated: false }),

            updateUser: (patch) =>
                set((s) => ({
                    user: s.user ? { ...s.user, ...patch } : null,
                })),
        }),
        {
            name: "app-auth",
            version: 1,
            migrate: () => ({
                token: null,
                user: null,
                isAuthenticated: false,
                setAuth: () => {},
                logout: () => {},
                updateUser: () => {},
            }),
        },
    ),
);
