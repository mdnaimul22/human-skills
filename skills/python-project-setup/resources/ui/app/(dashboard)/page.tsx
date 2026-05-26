import { PageHeader } from "@/components/layout/page-header";

/**
 * Dashboard Home — landing page after login.
 * Replace this placeholder with your actual dashboard content.
 */
export default function DashboardPage() {
    return (
        <>
            <PageHeader
                title="Dashboard"
                description="Welcome to your application"
            />

            {/* Placeholder cards — replace with real content */}
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
        </>
    );
}
