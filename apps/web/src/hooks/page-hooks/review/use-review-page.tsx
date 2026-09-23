import type { ColumnDef } from "@tanstack/react-table";
import Link from "next/link";
import { useEffect, useMemo, useRef } from "react";
import { toast } from "sonner";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { Progress, ReviewStateCell } from "@/components/page-components/Review/ReviewCounts/ReviewCounts";
import { REVIEW_STATE_OPTIONS } from "@/constants/review.constant";
import { useMe } from "@/hooks/common/use-me";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useAssignReviewerMutation } from "@/hooks/react-query/use-query-review";
import { useUserOptionsQuery } from "@/hooks/react-query/use-query-user";
import type { ReviewDocument } from "@/interfaces/review.interface";
import { ApiError } from "@/lib/common/http";

// reviewers: the org's teachers and admins
const STAFF = { filters: { role: { value: ["teacher", "org_admin"] } } };

/** Columns, the "Của tôi" switch and reviewer assignment of the review list. */
export function useReviewPage() {
  const me = useMe();
  const tq = useTableQuery();
  const canAssign = me.role === "org_admin";
  const { data: staff } = useUserOptionsQuery(STAFF, canAssign);
  const { mutateAsync: assignReviewer } = useAssignReviewerMutation();
  const mine = tq.get("mine") === "true";

  // the list opens on the papers that still need work (AC-01); once, so "Tất cả" is not taken back
  const seeded = useRef(false);
  const state = tq.get("review_state");
  useEffect(() => {
    if (seeded.current) return;
    seeded.current = true;
    if (!state) tq.setFilter("review_state", "pending");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const columns = useMemo<ColumnDef<ReviewDocument, unknown>[]>(() => {
    const options = (staff ?? []).map((t) => ({ value: t.id, label: t.full_name }));
    const onAssign = async (id: string, userId: string | null) => {
      try {
        await assignReviewer({ id, userId });
      } catch (e) {
        toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
      }
    };
    return [
      {
        id: "filename",
        header: "Đề",
        cell: ({ row }) => (
          <div className="max-w-[34rem]" data-testid={`rev-${row.original.document.filename}`}>
            <div className="font-medium break-words whitespace-normal">{row.original.document.filename}</div>
            <div className="text-xs text-muted-foreground">{row.original.total} câu</div>
          </div>
        ),
        meta: { filter: { kind: "text" }, sort: "filename" },
      },
      {
        id: "review_state",
        header: "Trạng thái",
        cell: ({ row }) => <ReviewStateCell r={row.original} />,
        meta: { filter: { kind: "select", options: REVIEW_STATE_OPTIONS }, sort: "review_state" },
      },
      { id: "progress", header: "Tiến độ", cell: ({ row }) => <Progress value={row.original.progress} /> },
      {
        id: "assigned_to",
        header: "Người duyệt",
        cell: ({ row }) =>
          canAssign ? (
            <OptionSelect
              size="sm"
              aria-label="Người duyệt"
              value={row.original.assigned_to ?? ""}
              onValueChange={(v) => void onAssign(row.original.document.id, v || null)}
              options={options}
              emptyLabel="— Chưa giao —"
              className="w-44"
            />
          ) : (
            <span className="text-sm text-muted-foreground">{row.original.assigned_name ?? "—"}</span>
          ),
        meta: canAssign ? { filter: { kind: "select", options } } : undefined,
      },
      {
        id: "action",
        header: "",
        cell: ({ row }) => (
          <Link href={`/org/review/${row.original.document.id}`} className="font-medium whitespace-nowrap text-primary hover:underline" onClick={(e) => e.stopPropagation()}>
            {row.original.pending ? `Duyệt ${row.original.pending} câu` : "Xem"}
          </Link>
        ),
        meta: { align: "right" },
      },
    ];
  }, [staff, canAssign, assignReviewer]);

  // "Của tôi" lives in the URL and goes to the server as a resource parameter
  const params = useMemo(() => (mine ? { mine: true } : {}), [mine]);

  return { columns, params, mine, setMine: (on: boolean) => tq.setFilter("mine", on ? "true" : null) };
}
