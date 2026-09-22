"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listHref } from "@/lib/common/list-memory";

/** "← <list>" link that returns to the list as it was left (page, sort, filters). */
export function BackLink({ href, children }: { href: string; children: React.ReactNode }) {
  const [to, setTo] = useState(href);
  useEffect(() => setTo(listHref(href)), [href]);
  return (
    <Link href={to} className="text-sm text-muted-foreground hover:underline">
      ← {children}
    </Link>
  );
}
