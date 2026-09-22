"use client";

import Link from "next/link";
import { Panel } from "@/components/common/Panel/Panel";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import type { PracticeItem } from "@/interfaces/practice.interface";
import { fmt } from "@/lib/common/dates";

/** The student's last practice attempts and why their questions were chosen. */
export function PracticeHistory({ items }: { items: PracticeItem[] | undefined }) {
  if (!items || !items.length) return null;
  return (
    <Panel>
      <h2 className="mb-2 font-medium">Lịch sử ôn tập</h2>
      <ul className="divide-y divide-border text-sm" data-testid="practice-history">
        {items.map((p) => (
          <li key={p.attempt_id} className="py-2">
            <div className="flex items-center justify-between gap-2">
              <span>
                {fmt(p.started_at)} {p.score10 !== null && <ToneBadge tone="blue">{p.score10} điểm</ToneBadge>}
              </span>
              <Link className="text-primary hover:underline" href={p.status === "submitted" ? `/results/${p.attempt_id}` : `/exam/${p.attempt_id}`}>
                {p.status === "submitted" ? "Xem kết quả" : "Làm tiếp"}
              </Link>
            </div>
            <div className="mt-1 flex flex-wrap gap-1 text-xs text-muted-foreground">
              {p.groups.map((g) => (
                <span key={`${g.reason}-${g.topic}`} className="rounded bg-muted px-2 py-0.5">
                  {g.reason}
                  {g.topic ? `: ${g.topic}` : ""} × {g.count}
                </span>
              ))}
            </div>
            {p.note && <p className="mt-1 text-xs text-muted-foreground">{p.note}</p>}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
