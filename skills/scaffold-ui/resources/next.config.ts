import type { NextConfig } from "next";
import fs from "fs";
import path from "path";

// Load parent .env if it exists
const envPath = path.resolve(__dirname, "../.env");
const env: Record<string, string> = {};

if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, "utf-8");
    content.split(/\r?\n/).forEach((line) => {
        const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
        if (match) {
            const key = match[1];
            let value = match[2] || "";
            if (value.startsWith('"') && value.endsWith('"')) {
                value = value.slice(1, -1);
            } else if (value.startsWith("'") && value.endsWith("'")) {
                value = value.slice(1, -1);
            }
            env[key] = value.trim();
        }
    });
}

// Build the API URL dynamically (Single Source of Truth)
const apiHost = env.API_HOST || "127.0.0.1";
const apiPort = env.API_PORT || "8000";
const apiUrl = `http://${apiHost}:${apiPort}`;

const nextConfig: NextConfig = {
    env: {
        NEXT_PUBLIC_API_URL: apiUrl,
    },
};

export default nextConfig;
