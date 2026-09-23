"use client";

import { Panel } from "@/components/common/Panel/Panel";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableFooter, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SECTION_LABEL } from "@/constants/exam.constant";
import { TYPE_LABEL } from "@/constants/question.constant";
import { useExamWeighting } from "@/hooks/page-hooks/exam-detail/use-exam-weighting";
import type { Exam } from "@/interfaces/exam.interface";
import { formatPoints as f } from "@/lib/page-libs/exam-detail/weighting";

/** "Thang điểm của đề": what each part is worth, what the paper is worth and what that becomes on the
 *  10-point scale — next to the inputs that set it (review-ux AC-06). Reads the exam payload only. */
export function ExamWeighting({ exam }: { exam: Pick<Exam, "questions" | "settings"> }) {
  const w = useExamWeighting(exam);

  return (
    <Panel id="thang-diem" data-testid="exam-weighting" className="min-w-0 p-4 sm:p-5">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-medium">Thang điểm của đề</h2>
        <Button asChild size="sm" variant="outline">
          <a href="#diem-mac-dinh">Sửa điểm mặc định theo loại</a>
        </Button>
      </div>
      {w.count === 0 ? (
        <p className="text-sm text-muted-foreground">Chưa có câu nào — điểm mỗi phần hiện theo điểm mặc định của loại câu.</p>
      ) : (
        <>
          <Table className="text-xs sm:text-sm">
            <TableHeader>
              <TableRow>
                <TableHead>Phần</TableHead>
                <TableHead className="text-right">Số câu</TableHead>
                <TableHead className="text-right">Điểm/câu</TableHead>
                <TableHead className="text-right">
                  Tổng<span className="hidden sm:inline"> phần</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {w.sections.map((s) => (
                <TableRow key={s.section} data-testid={`weight-${s.section}`}>
                  <TableCell>
                    <div className="font-medium">{SECTION_LABEL[s.section] ?? s.section}</div>
                    <div className="text-xs text-muted-foreground">{s.types.map((t) => TYPE_LABEL[t]).join(", ")}</div>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{s.count}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {s.perQuestion === null ? (
                      <>
                        {f(s.defaultPoints)} <span className="text-xs text-muted-foreground">(có câu khác)</span>
                      </>
                    ) : (
                      f(s.perQuestion)
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium tabular-nums">{f(s.total)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
            <TableFooter>
              <TableRow data-testid="weight-total">
                <TableCell className="font-medium">Cả đề</TableCell>
                <TableCell className="text-right tabular-nums">{w.count}</TableCell>
                <TableCell className="text-right text-muted-foreground">tổng thô</TableCell>
                <TableCell className="text-right font-semibold tabular-nums">{f(w.raw)}</TableCell>
              </TableRow>
            </TableFooter>
          </Table>
          <p className="mt-3 text-sm" data-testid="weight-scale">
            {w.exact ? (
              <>
                Tổng thô <strong className="tabular-nums">{f(w.raw)}</strong> điểm — đã đúng thang {f(w.scaleTo)}, không phải quy đổi.
              </>
            ) : (
              <>
                Tổng thô <strong className="tabular-nums">{f(w.raw)}</strong> điểm, quy về thang <strong className="tabular-nums">{f(w.scaleTo)}</strong>: mỗi điểm thô thành{" "}
                <strong className="tabular-nums">{f(w.factor ?? 0)}</strong> điểm ({f(w.scaleTo)} ÷ {f(w.raw)}).
              </>
            )}
          </p>
          {w.odd.length > 0 && (
            <div className="mt-3 rounded-md border border-amber-500/40 bg-amber-500/5 p-2 text-sm" data-testid="weight-odd">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <ToneBadge tone="amber">{w.odd.length} câu lệch điểm mặc định</ToneBadge>
                <span className="text-muted-foreground">Điểm của câu đã sửa riêng; đổi điểm mặc định của loại sẽ ghi đè lại:</span>
              </div>
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {w.odd.map((o) => (
                  <a key={o.id} href={`#points-${o.id}`} className="underline underline-offset-2 tabular-nums">
                    Câu {o.position}: {f(o.points)} thay vì {f(o.expected)}
                  </a>
                ))}
              </div>
            </div>
          )}
          <p className="mt-3 text-sm text-muted-foreground">
            Điểm từng câu sửa trực tiếp ở{" "}
            <a href="#cau-hoi-trong-de" className="underline underline-offset-2">
              Câu hỏi trong đề
            </a>
            ; điểm mặc định của mỗi loại ở{" "}
            <a href="#diem-mac-dinh" className="underline underline-offset-2">
              Điểm mặc định theo loại câu
            </a>
            .
          </p>
        </>
      )}
    </Panel>
  );
}
