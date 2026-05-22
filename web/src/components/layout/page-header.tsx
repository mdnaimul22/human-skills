interface PageHeaderProps {
    title: string;
    description?: string;
    children?: React.ReactNode;
}

/**
 * Page Header — Title + description + action buttons.
 *
 * @example
 *   <PageHeader title="Users" description="Manage all users">
 *     <Button>Add User</Button>
 *   </PageHeader>
 */
export function PageHeader({ title, description, children }: PageHeaderProps) {
    return (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6">
            <div>
                <h1 className="text-2xl font-bold text-[var(--color-text)] tracking-tight">
                    {title}
                </h1>
                {description && (
                    <p className="text-sm text-[var(--color-text-muted)] mt-1">
                        {description}
                    </p>
                )}
            </div>
            {children && (
                <div className="flex items-center gap-2 shrink-0">
                    {children}
                </div>
            )}
        </div>
    );
}
