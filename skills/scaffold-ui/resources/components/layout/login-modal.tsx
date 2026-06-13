"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

interface LoginModalProps {
    isOpen: boolean;
    onClose: () => void;
    defaultMode?: "login" | "register";
}

/**
 * LoginModal — Dialog overlay wrapping the auth form.
 * Opens on-screen without redirecting. Closes on Escape or backdrop click.
 */
export function LoginModal({ isOpen, onClose, defaultMode = "login" }: LoginModalProps) {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    // Close on Escape key
    useEffect(() => {
        if (!isOpen) return;
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
        };
        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [isOpen, onClose]);

    // Prevent body scroll when open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "";
        }
        return () => {
            document.body.style.overflow = "";
        };
    }, [isOpen]);

    if (!isOpen || !mounted) return null;

    return createPortal(
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200"
            onClick={(e) => {
                /* Close on backdrop click */
                if (e.target === e.currentTarget) onClose();
            }}
        >
            <div
                className="max-w-md w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-8 shadow-[var(--shadow-lg)] animate-in fade-in zoom-in-95 duration-200"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Close button */}
                <div className="flex justify-end mb-2">
                    <button
                        onClick={onClose}
                        className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-[var(--color-primary-light)] text-[var(--color-text-muted)] transition-colors cursor-pointer"
                        aria-label="Close"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                            <path d="M18 6L6 18M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Inline LoginForm — avoids redirect */}
                <InlineAuthForm defaultMode={defaultMode} onSuccess={onClose} />
            </div>
        </div>,
        document.body
    );
}

/* ── Inline Auth Form (extracted pattern from LoginForm) ──────── */

import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/components/layout/toast";
import { api, ApiError } from "@/lib/api";

interface TokenResponse {
    token: string;
    user_id: string;
    name: string;
    email: string;
}

function InlineAuthForm({ defaultMode, onSuccess }: { defaultMode: "login" | "register"; onSuccess: () => void }) {
    const [isRegister, setIsRegister] = useState(defaultMode === "register");
    const [email, setEmail] = useState("");
    const [name, setName] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const { setAuth } = useAuth();
    const { add: addToast } = useToast();

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
            const body = isRegister ? { email, name, password } : { email, password };
            const res = await api.post<TokenResponse>(endpoint, body);

            const profile = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/auth/me`,
                { headers: { Authorization: `Bearer ${res.token}` } },
            ).then((r) => r.json());

            setAuth(res.token, profile);
            addToast(isRegister ? "Account created!" : "Welcome back!", "success");
            onSuccess();
        } catch (err) {
            if (isRegister && err instanceof ApiError && err.status === 409) {
                setError("Email already registered. Switching to Sign In...");
                setTimeout(() => {
                    setIsRegister(false);
                    setError(null);
                }, 2000);
            } else if (!isRegister && err instanceof ApiError && (err.status === 401 || err.status === 400)) {
                setError("Incorrect email or password.");
                setPassword(""); // Clear password field
                document.getElementById("modal-password-input")?.focus();
            } else {
                const msg = err instanceof ApiError ? err.getDetail() : "Something went wrong";
                setError(msg);
            }
        } finally {
            setLoading(false);
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-5">
            <div className="text-center mb-4">
                <h2 className="text-xl font-bold text-[var(--color-text)]">
                    {isRegister ? "Create Account" : "Welcome Back"}
                </h2>
                <p className="text-sm text-[var(--color-text-muted)] mt-1">
                    {isRegister ? "Create an account to get started." : "Sign in to your workspace."}
                </p>
            </div>

            {isRegister && (
                <div>
                    <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">Name</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Your name"
                        required
                        className="w-full h-10 px-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-input)] text-[var(--color-text)] text-sm placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] outline-none transition-colors"
                    />
                </div>
            )}

            <div>
                <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">Email</label>
                <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                    className="w-full h-10 px-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-input)] text-[var(--color-text)] text-sm placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] outline-none transition-colors"
                />
            </div>

            <div>
                <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">Password</label>
                <div className="relative">
                    <input
                        id="modal-password-input"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        className="w-full h-10 pl-3 pr-10 rounded-lg border border-[var(--color-border)] bg-[var(--color-input)] text-[var(--color-text)] text-sm placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] outline-none transition-colors"
                    />
                    <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                        {showPassword ? (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                                <line x1="1" y1="1" x2="23" y2="23"></line>
                            </svg>
                        ) : (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                        )}
                    </button>
                </div>
            </div>

            {error && (
                <div className="p-3 rounded-lg bg-[var(--color-danger-light,rgba(239,68,68,0.15))] border border-[var(--color-danger)] text-[var(--color-danger)] text-xs font-medium text-center animate-in fade-in duration-200">
                    {error}
                </div>
            )}

            <button
                type="submit"
                disabled={loading}
                className="w-full h-11 rounded-lg bg-[var(--color-primary)] text-[var(--color-primary-foreground)] text-sm font-semibold hover:opacity-90 disabled:opacity-40 transition-opacity cursor-pointer"
            >
                {loading ? "Please wait..." : isRegister ? "Create Account" : "Sign In"}
            </button>

            <p className="text-center text-sm text-[var(--color-text-muted)]">
                {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
                <button
                    type="button"
                    onClick={() => setIsRegister(!isRegister)}
                    className="text-[var(--color-primary)] font-medium hover:underline cursor-pointer"
                >
                    {isRegister ? "Sign in" : "Sign up"}
                </button>
            </p>
        </form>
    );
}
