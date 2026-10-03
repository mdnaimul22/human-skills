import { ReactNode, useEffect } from 'react';

/**
 * ThemeProvider — applies the saved theme on mount.
 * Theme state is managed by useTheme() in user-menu.tsx via localStorage.
 */
export function ThemeProvider({
  children,
  defaultTheme = 'custom',
}: {
  children: ReactNode;
  defaultTheme?: string;
}) {
  useEffect(() => {
    const root = document.documentElement;
    const saved = localStorage.getItem('ext-theme') || defaultTheme;
    root.setAttribute('data-theme', saved);
    root.classList.add('theme-loaded');
  }, [defaultTheme]);

  return <>{children}</>;
}
