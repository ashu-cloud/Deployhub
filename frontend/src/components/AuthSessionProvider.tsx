"use client";

import { useEffect } from "react";
import { bootstrapSession } from "@/lib/api";

export function AuthSessionProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    void bootstrapSession();
  }, []);
  return <>{children}</>;
}
