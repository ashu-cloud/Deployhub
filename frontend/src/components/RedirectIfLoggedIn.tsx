"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { bootstrapSession } from "@/lib/api";

export function RedirectIfLoggedIn() {
  const router = useRouter();

  useEffect(() => {
    bootstrapSession().then((isLoggedIn) => {
      if (isLoggedIn) {
        router.push("/dashboard");
      }
    });
  }, [router]);

  return null;
}
