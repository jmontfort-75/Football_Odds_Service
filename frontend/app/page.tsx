"use client";

import { useEffect, useState } from "react";

type BackendState =
  | { kind: "loading" }
  | { kind: "healthy"; service: string }
  | { kind: "unreachable" };

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [backend, setBackend] = useState<BackendState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_BASE_URL}/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`Unexpected status ${res.status}`);
        return res.json();
      })
      .then((data: { status: string; service: string }) => {
        if (!cancelled) setBackend({ kind: "healthy", service: data.service });
      })
      .catch(() => {
        if (!cancelled) setBackend({ kind: "unreachable" });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 px-6 font-sans dark:bg-black">
      <main className="flex w-full max-w-md flex-col items-center gap-6 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-black dark:text-zinc-50">
          Football Odds Service
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Monitoring UI for the odds collection backend.
        </p>
        <BackendStatus state={backend} />
      </main>
    </div>
  );
}

function BackendStatus({ state }: { state: BackendState }) {
  if (state.kind === "loading") {
    return (
      <div className="rounded-full bg-zinc-200 px-4 py-2 text-sm text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
        Backend status: Checking…
      </div>
    );
  }

  if (state.kind === "healthy") {
    return (
      <div className="rounded-full bg-green-100 px-4 py-2 text-sm text-green-800 dark:bg-green-900/40 dark:text-green-300">
        Backend status: Healthy ({state.service})
      </div>
    );
  }

  return (
    <div className="rounded-full bg-red-100 px-4 py-2 text-sm text-red-800 dark:bg-red-900/40 dark:text-red-300">
      Backend status: Unreachable — is the FastAPI server running on{" "}
      {API_BASE_URL}?
    </div>
  );
}
