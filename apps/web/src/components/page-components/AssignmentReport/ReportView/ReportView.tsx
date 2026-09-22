import Link from "next/link";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Panel } from "@/components/app/Panel";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { REPORT_STATUS_LABEL } from "@/constants/assignment.constant";
import { TYPE_LABEL } from "@/constants/question.constant";
import type { AssignmentReport } from "@/interfaces/assignment.interface";
import { pct } from "@/lib/page-libs/assignment-report/pct";

export function ReportView({ report }: { report: AssignmentReport }) {
  const maxBucket = Math.max(1, ...report.distribution.map((b) => b.count));
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Panel>
          <div className="text-sm text-muted-foreground">Đã nộp</div>
          <div className="text-2xl font-semibold" data-testid="submitted">
            {report.submitted}/{report.total_students}
          </div>
        </Panel>
        <Panel>
          <div className="text-sm text-muted-foreground">Điểm trung bình</div>
          <div className="text-2xl font-semibold" data-testid="average">
            {report.average ?? "—"}
          </div>
        </Panel>
        <Panel>
          <div className="mb-1 text-sm text-muted-foreground">Phổ điểm</div>
          <div className="flex h-16 items-end gap-1" data-testid="distribution">
            {report.distribution.map((b) => (
              <div key={b.from} className="flex-1" title={`${b.from}–${b.to}: ${b.count}`}>
                <div className="rounded-t bg-primary" style={{ height: `${(b.count / maxBucket) * 56}px` }} />
                <div className="text-center text-[10px] text-muted-foreground/70">{b.from}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
      <Panel>
        <h2 className="mb-2 font-medium">Học sinh</h2>
        <div className="rounded-lg border bg-card">
          <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Học sinh</TableHead>
              <TableHead>Trạng thái</TableHead>
              <TableHead>Điểm</TableHead>
              <TableHead>Rời tab</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.students.map((s) => (
              <TableRow key={s.student_id} data-testid={`st-${s.username}`}>
                <TableCell>
                  {s.full_name} <span className="font-mono text-xs text-muted-foreground">{s.username}</span>
                </TableCell>
                <TableCell>
                  <ToneBadge tone={s.status === "submitted" ? "green" : s.status === "in_progress" ? "amber" : "gray"}>{REPORT_STATUS_LABEL[s.status]}</ToneBadge>
                  {s.needs_grading && <span className="ml-1"><ToneBadge tone="amber">Cần chấm tự luận</ToneBadge></span>}
                </TableCell>
                <TableCell>{s.score10 ?? "—"}</TableCell>
                <TableCell>{s.tab_switches || ""}</TableCell>
                <TableCell>
                  {s.attempt_id && s.status === "submitted" && (
                    <Link href={`/results/${s.attempt_id}`} className="text-primary hover:underline">
                      Xem bài
                    </Link>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          </Table>
        </div>
      </Panel>
      <Panel>
        <h2 className="mb-2 font-medium">Theo câu hỏi</h2>
        <ul className="divide-y divide-border">
          {report.questions.map((q) => (
            <li key={q.question_id} className="flex gap-3 py-2 text-sm" data-testid={`qs-${q.position}`}>
              <span className="w-8 font-semibold">{q.position}.</span>
              <div className="line-clamp-2 min-w-0 flex-1">
                <Markdown>{q.stem}</Markdown>
              </div>
              <span className="w-24 text-xs text-muted-foreground">{TYPE_LABEL[q.type]}</span>
              <span className="w-12 text-right font-medium">{pct(q.ratio)}</span>
              <span className="w-32 text-xs text-destructive">{q.top_wrong ? `Hay chọn sai: ${q.top_wrong.label} (${q.top_wrong.count})` : ""}</span>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
