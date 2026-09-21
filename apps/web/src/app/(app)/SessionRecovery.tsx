"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Access cookie expired: try the refresh cookie once, then fall back to /login. */
export function SessionRecovery() {
  const router = useRouter();
  useEffect(() => {
    fetch("/api/auth/refresh", { method: "POST", credentials: "include" }).then((r) => {
      if (r.ok) router.refresh();
      else window.location.assign("/login");
    });
  }, [router]);
  return <div className="p-8 text-sm text-gray-500">Đang tải…</div>;
}
