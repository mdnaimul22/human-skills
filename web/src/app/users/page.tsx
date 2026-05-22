import { AppShell } from "@/components/layout/app-shell";

export default function UsersPage() {
    return (
        <AppShell title="Users" description="Manage all users">
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-12 text-center">
                <p className="text-[var(--color-text-muted)]">
                    Connect your backend API to display users here.
                </p>
            </div>
        </AppShell>
    );
}
