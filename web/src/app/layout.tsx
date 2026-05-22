import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Poppins, Roboto } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { ThemeLoadedScript } from "@/components/layout/theme-loaded-script";
import "./globals.css";

/**
 * Font loading — preloaded and self-hosted via next/font.
 * This avoids external network requests and FOUT (Flash of Unstyled Text).
 */
const inter = Inter({
    subsets: ["latin"],
    variable: "--font-sans",
    display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
    subsets: ["latin"],
    variable: "--font-mono",
    display: "swap",
});

const poppins = Poppins({
    subsets: ["latin"],
    weight: ["300", "400", "500", "600", "700"],
    variable: "--font-poppins",
    display: "swap",
});

const roboto = Roboto({
    subsets: ["latin"],
    variable: "--font-roboto",
    display: "swap",
});

export const metadata: Metadata = {
    title: "Dashboard",
    description: "Application Dashboard",
};

/**
 * Root Layout
 *
 * Anti-flicker strategy:
 * 1. `suppressHydrationWarning` on <html> — prevents React hydration
 *    mismatch warning since next-themes injects data-theme before hydration.
 * 2. next-themes reads theme from localStorage BEFORE first paint via
 *    an inline <script> (injected automatically by ThemeProvider).
 * 3. `body.theme-loaded` class is added after mount to enable smooth
 *    background-color transitions (prevented on first load to avoid flicker).
 * 4. `enableSystem={false}` — we control themes explicitly, no OS detection
 *    race condition.
 */
export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html
            lang="en"
            suppressHydrationWarning
            className={`${inter.variable} ${jetbrainsMono.variable} ${poppins.variable} ${roboto.variable}`}
        >
            <body>
                <ThemeProvider
                    attribute="data-theme"
                    defaultTheme="dark"
                    enableSystem={false}
                    themes={[
                        "dark",
                        "matrix",
                        "cream",
                        "matte-black",
                        "black-brown",
                        "jam-black",
                        "jam-navy",
                        "light",
                        "snow",
                    ]}
                    disableTransitionOnChange={false}
                >
                    {children}
                </ThemeProvider>
                <ThemeLoadedScript />
            </body>
        </html>
    );
}
