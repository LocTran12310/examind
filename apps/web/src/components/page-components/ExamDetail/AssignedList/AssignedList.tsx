import Link from "next/link";
import { Panel } from "@/components/common/Panel/Panel";
import type { Assignment } from "@/interfaces/assignment.interface";
import { formatDateTime } from "@/lib/common/datetime";

/** "Đã giao": the assignments of this exam with their classes, window and submissions. */
export function AssignedList({ assigned }: { assigned: Assignment[] }) {
  if (!assigned.length) return null;
  return (
    <Panel>
      <h2 className="mb-2 font-medium">Đã giao</h2>
      <ul className="divide-y divide-border text-sm" data-testid="assigned">
        {assigned.map((a) => (
          <li key={a.id} className="flex items-center justify-between py-2">
            <span>
              <Link href={`/org/assignments/${a.id}`} className="font-medium text-primary hover:underline">
                {a.title}
              </Link>
              <span className="block text-xs text-muted-foreground">
                {a.classes.join(", ")} · {formatDateTime(a.open_at)} → {formatDateTime(a.close_at)}
              </span>
            </span>
            <span className="text-xs text-muted-foreground">
              {a.submitted}/{a.students} đã nộp
            </span>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
