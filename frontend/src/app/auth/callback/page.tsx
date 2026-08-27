"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { bootstrapSession } from "@/lib/api";

export default function AuthCallbackPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const ok = await bootstrapSession();
      if (cancelled) return;
      if (ok) {
        router.replace("/dashboard");
        return;
      }
      setError("Could not establish a session. Sign in again.");
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-on-surface font-mono text-sm">
      {error ? (
        <p className="text-on-surface-variant">Could not establish a session. Sign in again.</p>
      ) : (
        <p className="text-on-surface-variant">Signing you in…</p>
      )}
    </div>
  );
}
