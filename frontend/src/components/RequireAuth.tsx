"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { bootstrapSession } from "@/lib/api";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    bootstrapSession().then((isLoggedIn) => {
      if (!isLoggedIn) {
        router.push("/login");
      } else {
        setIsAuthenticated(true);
      }
    });
  }, [router]);

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-background text-on-surface paper-texture flex flex-col items-center justify-center font-mono">
        <div className="animate-pulse">Loading workspace...</div>
      </div>
    );
  }

  return <>{children}</>;
}
