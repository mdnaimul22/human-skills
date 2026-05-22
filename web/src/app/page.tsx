import { AppShell } from "@/components/layout/app-shell";

/**
 * Home Page — Dashboard
 */
export default function HomePage() {
    return (
        <AppShell title="Dashboard" description="Welcome to your application">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {[
                    { title: "Total Users", value: "—", icon: "👥" },
                    { title: "Active Now",  value: "—", icon: "🟢" },
                    { title: "Revenue",     value: "—", icon: "💰" },
                ].map((card) => (
                    <div
                        key={card.title}
                        className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-6 shadow-[var(--shadow-sm)] transition-shadow hover:shadow-[var(--shadow-md)]"
                    >
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-[var(--color-text-muted)]">
                                {card.title}
                            </p>
                            <span className="text-xl">{card.icon}</span>
                        </div>
                        <p className="mt-2 text-3xl font-bold text-[var(--color-text)] tracking-tight">
                            {card.value}
                        </p>
                    </div>
                ))}
            </div>
        </AppShell>
    );
}
