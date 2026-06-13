import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Poppins, Roboto, Outfit, Space_Grotesk } from "next/font/google";
import { ThemeProvider, ThemeLoadedScript } from "@/components/layout/theme";
import { ToastContainer } from "@/components/layout/toast";
import "./globals.css";

/**
 * Font loading — preloaded and self-hosted via next/font.
 * Avoids external network requests and FOUT (Flash of Unstyled Text).
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
    weight: ["400", "500", "600", "700"],
    subsets: ["latin"],
    variable: "--font-poppins",
    display: "swap",
});

const roboto = Roboto({
    weight: ["400", "500", "700"],
    subsets: ["latin"],
    variable: "--font-roboto",
    display: "swap",
});

const outfit = Outfit({
    subsets: ["latin"],
    variable: "--font-outfit",
    display: "swap",
});

const spaceGrotesk = Space_Grotesk({
    subsets: ["latin"],
    variable: "--font-space-grotesk",
    display: "swap",
});

export const metadata: Metadata = {
    title: {
        default: "Dashboard",
        template: "%s | App",
    },
    description: "Application Dashboard",
};

/**
 * Root Layout
 *
 * Anti-flicker strategy:
 * 1. `suppressHydrationWarning` on <html> — prevents React hydration
 *    mismatch warning since next-themes injects data-theme before hydration.
 * 2. next-themes reads theme from localStorage BEFORE first paint via
 *    an inline <script> injected automatically by ThemeProvider.
 * 3. `body.theme-loaded` class is added after mount (ThemeLoadedScript)
 *    to enable smooth background-color transitions after first paint.
 * 4. `enableSystem={false}` — themes are controlled explicitly, no OS
 *    detection race condition.
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
            className={`${inter.variable} ${jetbrainsMono.variable} ${poppins.variable} ${roboto.variable} ${outfit.variable} ${spaceGrotesk.variable}`}
        >
            <body suppressHydrationWarning>
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
                        "custom",
                        "claude",
                    ]}
                    disableTransitionOnChange={false}
                >
                    {children}
                    {/* Anti-flicker: enables background-color transition after first paint */}
                    <ThemeLoadedScript />
                    {/* Global toast notifications — BEW pattern */}
                    <ToastContainer />
                </ThemeProvider>
            </body>
        </html>
    );
}
