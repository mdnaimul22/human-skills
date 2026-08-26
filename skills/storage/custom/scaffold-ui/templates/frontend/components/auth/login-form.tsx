"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/components/layout/toast";
import { api, ApiError } from "@/lib/api";

interface TokenResponse {
    token: string;
    user_id: string;
    name: string;
    email: string;
}

/**
 * Login/Register Form — email + password with toggle.
 * Stores JWT token in Zustand auth store → persisted in localStorage.
 */
export function LoginForm() {
    const [isRegister, setIsRegister] = useState(false);
    const [email, setEmail] = useState("");
    const [name, setName] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const { setAuth } = useAuth();
    const { add: addToast } = useToast();
    const router = useRouter();

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
            const body = isRegister
                ? { email, name, password }
                : { email, password };

            const res = await api.post<TokenResponse>(endpoint, body);

            // Fetch full profile
            const profile = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/auth/me`,
                { headers: { Authorization: `Bearer ${res.token}` } },
            ).then((r) => r.json());

            setAuth(res.token, profile);
            addToast(isRegister ? "Account created!" : "Welcome back!", "success");
            router.push("/");
        } catch (err) {
            if (isRegister && err instanceof ApiError && err.status === 409) {
                setError("Email already registered. Switching to Sign In...");
                setTimeout(() => {
                    setIsRegister(false);
                    setError(null);
                }, 2000);
            } else if (!isRegister && err instanceof ApiError && (err.status === 401 || err.status === 400)) {
                setError("Incorrect email or password.");
                setPassword(""); // Clear password field for quick retry
                document.getElementById("password-input")?.focus();
            } else {
                const msg =
                    err instanceof ApiError ? err.getDetail() : "Network error";
                setError(msg);
            }
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="w-full max-w-sm space-y-6">
            {/* Header */}
            <div className="text-center">
                <h1 className="text-2xl font-bold text-[var(--color-text)] tracking-tight">
                    {isRegister ? "Create Account" : "Welcome Back"}
                </h1>
                <p className="text-sm text-[var(--color-text-muted)] mt-2">
                    {isRegister
                        ? "Create an account to get started"
                        : "Sign in to your workspace"}
                </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
                {isRegister && (
                    <div>
                        <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                            Name
                        </label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            placeholder="Your name"
                            className="w-full h-11 px-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-input)] text-[var(--color-text)] text-sm placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--ring-color)] outline-none transition-colors"
                        />
                    </div>
                )}

                <div>
                    <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                        Email
                    </label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        placeholder="you@example.com"
                        className="w-full h-11 px-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-input)] text-[var(--color-text)] text-sm placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--ring-color)] outline-none transition-colors"
                    />
                </div>

                <div>
                    <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                        Password
                    </label>
                    <div className="relative">
                        <input
                            id="password-input"
                            type={showPassword ? "text" : "password"}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            minLength={6}
                            placeholder="••••••••"
                            className="w-full h-11 pl-3 pr-10 rounded-lg border border-[var(--color-border)] bg-[var(--color-input)] text-[var(--color-text)] text-sm placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--ring-color)] outline-none transition-colors"
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
                            aria-label={showPassword ? "Hide password" : "Show password"}
                        >
                            {showPassword ? (
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                                    <line x1="1" y1="1" x2="23" y2="23"></line>
                                </svg>
                            ) : (
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                    className="w-full h-11 rounded-lg bg-[var(--color-primary)] text-[var(--color-primary-foreground)] text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity cursor-pointer"
                >
                    {loading ? (
                        <span className="inline-flex items-center gap-2">
                            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
                                <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className="opacity-75" />
                            </svg>
                            Processing...
                        </span>
                    ) : isRegister ? "Create Account" : "Sign In"}
                </button>
            </form>

            {/* Toggle */}
            <p className="text-center text-sm text-[var(--color-text-muted)]">
                {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
                <button
                    type="button"
                    onClick={() => setIsRegister(!isRegister)}
                    className="text-[var(--color-primary)] hover:underline font-medium cursor-pointer"
                >
                    {isRegister ? "Sign in" : "Sign up"}
                </button>
            </p>
        </div>
    );
}
