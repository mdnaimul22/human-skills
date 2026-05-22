"use client";

import { useEffect } from "react";

/**
 * Adds `theme-loaded` class to body after first paint.
 * This enables smooth background-color transitions AFTER
 * the initial theme is resolved — preventing flicker.
 *
 * Must be a client component because useEffect runs only in the browser.
 */
export function ThemeLoadedScript() {
    useEffect(() => {
        requestAnimationFrame(() => {
            document.body.classList.add("theme-loaded");
        });
    }, []);

    return null;
}
