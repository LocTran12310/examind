"use client";

import Link from "next/link";
import { Panel } from "@/components/common/Panel/Panel";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAttemptSearchQuery } from "@/hooks/react-query/use-query-attempts";

const when = (iso: string | null) =>
  iso ? new Date(iso).toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "—";

/** Em ấy đã làm những đề nào, lúc nào, mất bao lâu (AC-01, AC-02). */
export function AttemptHistory({ studentId }: { studentId: string }) {
  const { data } = useAttemptSearchQuery({ page: 1, limit: 50, filters: { student_id: { value: studentId } } });
  if (!data) return null;
  return (
    <Panel className="mt-6">
      <h2 className="mb-1 font-medium">Lịch sử làm bài</h2>
      <p className="mb-3 text-sm text-muted-foreground">
        Thời gian tính từ lúc bắt đầu tới lúc nộp, không phải tổng thời gian ở trên từng câu.
      </p>
      {data.data.length === 0 ? (
        <p className="text-sm text-muted-foreground">Em này chưa làm bài nào.</p>
      ) : (
        <Table data-testid="attempt-history">
          <TableHeader>
            <TableRow>
              <TableHead>Đề</TableHead>
              <TableHead>Bắt đầu</TableHead>
              <TableHead>Nộp</TableHead>
              <TableHead className="text-right">Thời gian</TableHead>
              <TableHead className="text-right">Điểm</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.data.map((r) => (
              <TableRow key={r.attempt_id} data-testid={`ah-${r.attempt_id}`}>
                <TableCell>
                  <Link href={`/results/${r.attempt_id}`} className="hover:text-primary">{r.exam_title}</Link>
                  {r.assignment_title && r.assignment_title !== r.exam_title && (
                    <span className="ml-1 text-xs text-muted-foreground">· {r.assignment_title}</span>
                  )}
                  {/* một lượt hệ thống tự đóng vẫn nằm đây, có dấu riêng: giấu nó đi thì cột thời gian nói dối
                      về đúng những lượt đáng chú ý nhất (AC-02) */}
                  {r.auto_submitted && <ToneBadge tone="amber" className="ml-2">tự nộp khi hết giờ</ToneBadge>}
                  {r.status !== "submitted" && <ToneBadge tone="gray" className="ml-2">đang làm</ToneBadge>}
                </TableCell>
                <TableCell className="whitespace-nowrap">{when(r.started_at)}</TableCell>
                <TableCell className="whitespace-nowrap">{when(r.submitted_at)}</TableCell>
                <TableCell className="text-right whitespace-nowrap">
                  {/* `null` là chưa nộp; `0` là nộp gần như tức thì. Hai điều khác nhau, nên hiện khác nhau. */}
                  {r.minutes === null ? "—" : `${r.minutes} phút`}
                </TableCell>
                <TableCell className="text-right">{r.score10 === null ? "—" : r.score10}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Panel>
  );
}
