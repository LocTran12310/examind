"use client";

import Link from "next/link";
import { useState } from "react";
import { Panel } from "@/components/common/Panel/Panel";
import { Button } from "@/components/ui/button";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import type { PracticeItem } from "@/interfaces/practice.interface";
import { fmt } from "@/lib/common/dates";

/** The number of runs shown before the list folds: enough to see what you did lately, short enough that the
 *  panels under it stay reachable without scrolling past a wall of history. */
const SHOWN = 3;

/** The student's last practice attempts and why their questions were chosen.
 *
 *  Folded to the last few by default. Every run a student does adds a row here, so after a term of practice the
 *  list pushes everything else off the screen — but the rows are the student's own record, so the answer is to
 *  fold them, not to let anything delete them. */
export function PracticeHistory({ items }: { items: PracticeItem[] | undefined }) {
  const [open, setOpen] = useState(false);
  if (!items || !items.length) return null;
  const shown = open ? items : items.slice(0, SHOWN);
  const hidden = items.length - shown.length;
  return (
    <Panel>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-medium">Lịch sử ôn tập</h2>
        {(hidden > 0 || open) && (
          <Button variant="ghost" size="sm" onClick={() => setOpen((v) => !v)}>
            {open ? "Thu gọn" : `Xem cả ${items.length} lượt`}
          </Button>
        )}
      </div>
      <ul className="divide-y divide-border text-sm" data-testid="practice-history">
        {shown.map((p) => (
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
      {hidden > 0 && <p className="mt-2 text-xs text-muted-foreground">Còn {hidden} lượt nữa.</p>}
    </Panel>
  );
}
