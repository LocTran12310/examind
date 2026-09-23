import type { ColumnDef } from "@tanstack/react-table";
import { Undo2 } from "lucide-react";
import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { EVENT_FIELD_LABEL, REVIEW_ACTION_LABEL } from "@/constants/question.constant";
import { useUndoBatch } from "@/hooks/page-hooks/bank/use-undo-batch";
import type { QuestionEvent } from "@/interfaces/question.interface";
import { formatDateTime } from "@/lib/common/datetime";

/** A batch a page of the list shows: its own id when it has one, else something stable to key the row by.
 *  Events written before batches existed are grouped by their own event id server-side but come back with
 *  `batch_id: null`, and they are read-only anyway. */
export const eventRowId = (e: QuestionEvent) => e.batch_id ?? `${e.created_at}·${e.action}·${e.user_id ?? ""}`;

/** The fields a batch moved, in the teacher's words; an unknown name is shown as the API sent it. */
export const fieldLabels = (fields: string[]) => fields.map((f) => EVENT_FIELD_LABEL[f] ?? f);

/** "Thay đổi gần đây": the columns of the history and the undo each row offers (AC-03, AC-04, AC-05).
 *  Nothing here decides whether a row can be taken back — `undoable` and its `message` come from the server,
 *  so after an undo the list simply says something else. */
export function useRecentChanges() {
  const undo = useUndoBatch();
  const columns = useMemo<ColumnDef<QuestionEvent, unknown>[]>(
    () => [
      { accessorKey: "created_at", header: "Thời điểm", cell: ({ row }) => formatDateTime(row.original.created_at), meta: { filter: { kind: "date" }, sort: "created_at", className: "w-40" } },
      { accessorKey: "actor_name", header: "Người sửa", cell: ({ row }) => row.original.actor_name ?? "Hệ thống" },
      { accessorKey: "action", header: "Thao tác", cell: ({ row }) => REVIEW_ACTION_LABEL[row.original.action] ?? row.original.action },
      {
        id: "fields",
        header: "Đã đổi",
        cell: ({ row }) => <span className="text-muted-foreground">{fieldLabels(row.original.fields).join(", ") || "—"}</span>,
      },
      { accessorKey: "questions", header: "Số câu", cell: ({ row }) => <span className="tabular-nums">{row.original.questions}</span>, meta: { align: "right", className: "w-20" } },
      {
        id: "undo",
        header: "",
        // the row is wider than a phone, and the way back must not be the part that scrolls off: it stays
        // pinned to the right edge, over the columns rather than after them
        meta: { align: "right", className: "sticky right-0 w-44 bg-inherit shadow-[inset_1px_0_0_var(--border)]" },
        cell: ({ row }) => {
          const e = row.original;
          // a row that cannot be taken back keeps its place and says why, in the API's own sentence: the list is
          // a record of what happened, and a reason read once is what stops the teacher looking for the button
          if (!e.undoable || !e.batch_id) return <span className="text-xs text-muted-foreground">{e.message ?? "Không hoàn tác được"}</span>;
          return (
            <Button variant="outline" size="xs" disabled={undo.undoing !== null} onClick={() => void undo.run(e.batch_id!)}>
              <Undo2 /> Hoàn tác
            </Button>
          );
        },
      },
    ],
    [undo],
  );
  return { columns, undo };
}
