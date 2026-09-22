"use client";

import { useSessionRecovery } from "@/hooks/page-hooks/layout/use-session-recovery";

/** Access cookie expired: try the refresh cookie once, then fall back to /login. */
export function SessionRecovery() {
  useSessionRecovery();
  return <div className="p-8 text-sm text-muted-foreground">Đang tải…</div>;
}
