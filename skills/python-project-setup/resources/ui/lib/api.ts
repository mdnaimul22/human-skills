/**
 * Secure FastAPI API client.
 *
 * Security measures:
 * - All responses are validated (non-2xx throws)
 * - Content-Type is enforced
 * - Credentials are included for httpOnly cookie auth
 * - Request timeout prevents hanging connections
 * - No eval() or innerHTML — JSON.parse only
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 15_000;

/** Custom API error with status code and response body */
export class ApiError extends Error {
    constructor(
        public readonly status: number,
        public readonly statusText: string,
        public readonly body: unknown,
    ) {
        super(`API Error ${status}: ${statusText}`);
        this.name = "ApiError";
    }
}

/**
 * Type-safe fetch wrapper for FastAPI backend.
 *
 * @example
 *   const users = await apiFetch<User[]>("/api/users");
 *   const user  = await apiFetch<User>("/api/users", { method: "POST", body: JSON.stringify(data) });
 */
export async function apiFetch<T>(
    endpoint: string,
    options?: RequestInit,
): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                "Content-Type": "application/json",
                ...options?.headers,
            },
            credentials: "include",   // httpOnly cookie auth — no localStorage tokens
            signal: controller.signal,
            ...options,
        });

        if (!res.ok) {
            const body = await res.json().catch(() => null);
            throw new ApiError(res.status, res.statusText, body);
        }

        return (await res.json()) as T;
    } finally {
        clearTimeout(timeout);
    }
}

/**
 * Convenience methods matching FastAPI router patterns.
 */
export const api = {
    get: <T>(endpoint: string) => apiFetch<T>(endpoint),

    post: <T>(endpoint: string, data: unknown) =>
        apiFetch<T>(endpoint, {
            method: "POST",
            body: JSON.stringify(data),
        }),

    put: <T>(endpoint: string, data: unknown) =>
        apiFetch<T>(endpoint, {
            method: "PUT",
            body: JSON.stringify(data),
        }),

    patch: <T>(endpoint: string, data: unknown) =>
        apiFetch<T>(endpoint, {
            method: "PATCH",
            body: JSON.stringify(data),
        }),

    delete: <T>(endpoint: string) =>
        apiFetch<T>(endpoint, { method: "DELETE" }),
} as const;
