import { AppShell } from "@/components/layout/app-shell";

/**
 * Root page — scaffold starting point.
 * Replace this with your application's landing page.
 */
export default function Home() {
    return (
        <AppShell>
            <div className="flex flex-1 items-center justify-center">
                <p className="text-sm text-[var(--color-text-muted)]">
                    Start building your app here.
                </p>
            </div>
        </AppShell>
    );
}
