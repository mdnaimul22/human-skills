/**
 * Public route group layout — passthrough.
 * Pages here are accessible without authentication.
 */
export default function PublicLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
