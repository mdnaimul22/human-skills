import Link from "next/link";

/**
 * 404 — Not Found page.
 * Next.js automatically renders this for any unmatched route.
 */
export default function NotFound() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)] p-4">
            <div className="text-center space-y-4">
                <p className="text-7xl font-bold text-[var(--color-primary)] tracking-tight">
                    404
                </p>
                <h1 className="text-xl font-semibold text-[var(--color-text)]">
                    Page not found
                </h1>
                <p className="text-sm text-[var(--color-text-muted)] max-w-xs mx-auto">
                    The page you&apos;re looking for doesn&apos;t exist or has been moved.
                </p>
                <Link
                    href="/"
                    className="inline-flex h-10 items-center justify-center rounded-lg bg-[var(--color-primary)] px-6 text-sm font-medium text-[var(--color-primary-foreground)] hover:opacity-90 transition-opacity"
                >
                    Go home
                </Link>
            </div>
        </div>
    );
}
