/**
 * Secure FastAPI API client.
 *
 * Security measures:
 * - All responses are validated (non-2xx throws)
 * - Content-Type is enforced
 * - JWT Bearer auth from Zustand store
 * - Request timeout prevents hanging connections
 * - No eval() or innerHTML — JSON.parse only
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL!;
const REQUEST_TIMEOUT_MS = 30_000;

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

    /** Extract a human-readable error string from FastAPI responses. */
    getDetail(): string {
        const b = this.body as Record<string, unknown> | null;
        if (!b) return this.statusText;
        const errorVal = b.error || b.detail;
        if (typeof errorVal === "string") return errorVal;
        // Pydantic 422: detail is [{type, loc, msg, input, ctx}, ...]
        if (Array.isArray(errorVal) && errorVal.length > 0) {
            const first = errorVal[0];
            if (typeof first === "object" && first !== null && "msg" in first) {
                return String((first as Record<string, unknown>).msg);
            }
            return String(first);
        }
        return this.statusText;
    }
}

/**
 * Get auth token from localStorage (Zustand persist store).
 * Avoids circular dependency with hooks.
 */
function getToken(): string | null {
    try {
        const raw = localStorage.getItem("app-auth");
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        return parsed?.state?.token ?? null;
    } catch {
        return null;
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

    const token = getToken();
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options?.headers as Record<string, string>),
    };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers,
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
