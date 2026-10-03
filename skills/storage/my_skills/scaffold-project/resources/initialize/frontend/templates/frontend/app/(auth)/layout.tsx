/**
 * Auth Layout — NO sidebar, NO navbar.
 * Centered card on themed background.
 * Used for login, register, forgot-password pages.
 */
export default function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)] p-4">
            <div className="w-full max-w-md rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-8 shadow-[var(--shadow-lg)]">
                {children}
            </div>
        </div>
    );
}
