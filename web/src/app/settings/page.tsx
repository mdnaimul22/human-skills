import { AppShell } from "@/components/layout/app-shell";

export default function SettingsPage() {
    return (
        <AppShell title="Settings" description="Application settings">
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-12 text-center">
                <p className="text-[var(--color-text-muted)]">
                    Settings page — customize your application preferences.
                </p>
            </div>
        </AppShell>
    );
}
