import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";

export default function SettingsPage() {
    return (
        <AppShell>
            <PageHeader
                title="Settings"
                description="Application settings"
            />
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-12 text-center">
                <p className="text-[var(--color-text-muted)]">
                    Settings page — customize your application preferences.
                </p>
            </div>
        </AppShell>
    );
}
