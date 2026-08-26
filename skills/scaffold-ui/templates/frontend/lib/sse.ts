/**
 * SSE (Server-Sent Events) helper for real-time progress streaming.
 *
 * Usage:
 *   const sse = createSSE("/api/progress/abc123", {
 *     onProgress: (data) => setProgress(data),
 *     onComplete: (data) => handleDone(data),
 *     onError: (err) => handleError(err),
 *   });
 *   // Later: sse.close();
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL!;

interface SSEProgress {
    job_id: string;
    status: "received" | "queued" | "processing" | "complete" | "failed" | "timeout";
    progress: number;
    message: string;
    error: string | null;
    metadata?: Record<string, unknown>;
}

interface SSECallbacks {
    onProgress?: (data: SSEProgress) => void;
    onComplete?: (data: SSEProgress) => void;
    onError?: (error: string) => void;
}

export function createSSE(endpoint: string, callbacks: SSECallbacks) {
    const url = `${API_BASE}${endpoint}`;
    const source = new EventSource(url);
    let isClosed = false;

    source.onmessage = (event) => {
        if (isClosed) return;
        try {
            const data: SSEProgress = JSON.parse(event.data);

            if (data.status === "complete") {
                isClosed = true;
                callbacks.onComplete?.(data);
                source.close();
            } else if (data.status === "failed" || data.status === "timeout") {
                isClosed = true;
                callbacks.onError?.(data.error || data.message);
                source.close();
            } else {
                callbacks.onProgress?.(data);
            }
        } catch {
            // Skip unparseable messages (heartbeats)
        }
    };

    source.onerror = () => {
        if (isClosed) return;
        isClosed = true;
        callbacks.onError?.("Connection lost");
        source.close();
    };

    return {
        close: () => {
            isClosed = true;
            source.close();
        },
    };
}

export type { SSEProgress };
