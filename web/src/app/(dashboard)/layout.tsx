import { AppShell } from "@/components/layout/app-shell";

/**
 * Dashboard Layout — wraps all dashboard pages with Sidebar + Navbar.
 * Auth-protected pages live under this route group.
 */
export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <AppShell>{children}</AppShell>;
}
