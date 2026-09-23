"use client";

import { Search, Wand2 } from "lucide-react";
import { DebouncedInput } from "@/components/common/DataTable/FilterCell";
import { EmptyState } from "@/components/common/EmptyState/EmptyState";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { TopicPicker } from "@/components/common/TopicPicker/TopicPicker";
import { Button } from "@/components/ui/button";
import { DIFFICULTY_LABEL, TYPE_LABEL } from "@/constants/question.constant";
import { useSwapQuestion } from "@/hooks/page-hooks/exam-detail/use-swap-question";
import type { ExamQuestion } from "@/interfaces/exam.interface";
import { topicLabel } from "@/lib/common/topic-tree";
import { formatPoints } from "@/lib/page-libs/exam-detail/weighting";

export interface SwapQuestionDialogProps {
  question: ExamQuestion;
  subjectId: string | null;
  /** every question already in the exam: none of them can be chosen twice */
  inExam: Set<string>;
  /** the automatic replacement the builder has always done */
  onAuto: () => void;
  onChoose: (questionId: string) => void;
}

/** "Đổi câu": either the system picks the replacement as before, or the teacher searches the bank and
 *  chooses one — the position keeps its number and its points (ADR-03, AC-07). Only a question of the same
 *  type can take the place: the part of the paper and the default points both come from the type. */
export function SwapQuestionDialog({ question, subjectId, inExam, onAuto, onChoose }: SwapQuestionDialogProps) {
  const s = useSwapQuestion(question, subjectId);
  const byId = new Map(s.topics.map((t) => [t.id, t]));
  return (
    <div className="space-y-3" data-testid="swap-dialog">
      <div className="rounded-lg border border-border bg-muted/40 p-3">
        <div className="line-clamp-2 text-sm">
          <Markdown>{question.stem}</Markdown>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Câu {question.position} · {TYPE_LABEL[question.type]} · {formatPoints(question.points)} điểm — câu thay thế giữ nguyên vị trí và số điểm này.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outline" onClick={onAuto}>
          <Wand2 /> Để hệ thống chọn
        </Button>
        <span className="text-sm text-muted-foreground">hoặc tìm trong ngân hàng và tự chọn:</span>
      </div>
      <div className="grid gap-2 rounded-lg border border-border p-2 sm:grid-cols-2">
        <div className="relative sm:col-span-2">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <DebouncedInput aria-label="Tìm nội dung" className="pl-8" placeholder="Tìm nội dung câu hỏi (không cần dấu)…" value={s.q} onChange={s.setQ} />
        </div>
        <OptionSelect aria-label="Môn" value={s.subjectId} onValueChange={s.setSubject} emptyLabel="Mọi môn" options={s.subjects.map((x) => ({ value: x.id, label: x.name }))} />
        <Button variant="outline" className="min-w-0 justify-start font-normal" onClick={() => s.setPicking(!s.picking)}>
          <span className="truncate">{s.topic ? topicLabel(s.topic, byId) : "Mọi chuyên đề"}</span>
        </Button>
        <OptionSelect
          aria-label="Loại câu"
          value={s.type}
          onValueChange={s.setType}
          emptyLabel="Mọi loại"
          options={Object.entries(TYPE_LABEL).map(([k, v]) => ({ value: k, label: k === question.type ? v : `${v} (khác loại)` }))}
        />
        <OptionSelect
          aria-label="Mức độ"
          value={s.difficulty}
          onValueChange={s.setDifficulty}
          emptyLabel="Mọi mức độ"
          options={Object.entries(DIFFICULTY_LABEL).map(([k, v]) => ({ value: k, label: v }))}
        />
        <OptionSelect aria-label="Tag" value={s.tagId} onValueChange={s.setTagId} emptyLabel="Mọi tag" options={s.tags.map((t) => ({ value: t.id, label: t.name }))} />
        {s.picking && (
          <div className="sm:col-span-2">
            <TopicPicker
              topics={s.topics}
              counts={s.counts}
              autoFocus={false}
              initial={s.topicId ?? question.topics.find((t) => t.is_primary)?.id ?? null}
              onPick={(t) => {
                s.setTopicId(t.id);
                s.setPicking(false);
              }}
              onClose={() => s.setPicking(false)}
            />
            {s.topicId && (
              <Button variant="ghost" size="sm" className="mt-1" onClick={() => s.setTopicId(null)}>
                Bỏ lọc chuyên đề
              </Button>
            )}
          </div>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        Chỉ chọn được câu cùng loại ({TYPE_LABEL[question.type]}): phần của đề và điểm mặc định đều theo loại câu. Muốn dùng câu khác loại thì bỏ câu này rồi thêm câu đó
        từ ngân hàng — đề sẽ tự xếp lại phần và điểm.
      </p>
      {s.loaded && s.found.length === 0 && <EmptyState>Không có câu hỏi phù hợp.</EmptyState>}
      {s.found.length > 0 && (
        <>
          <p className="text-xs text-muted-foreground">
            {s.total.toLocaleString("vi-VN")} câu phù hợp{s.total > s.found.length ? ` — đang xem ${s.found.length} câu đầu, thu hẹp bộ lọc để thấy câu cần tìm` : ""}
          </p>
          <ul className="divide-y divide-border rounded-lg border border-border" data-testid="swap-results">
            {s.found.map((x) => {
              const already = inExam.has(x.id);
              const other = x.type !== question.type;
              const primary = x.topics.find((t) => t.is_primary);
              return (
                <li key={x.id} className="flex items-start gap-3 p-3" data-testid={`swap-${x.id}`}>
                  <div className="min-w-0 flex-1">
                    <div className="line-clamp-3 text-sm">
                      <Markdown>{x.stem}</Markdown>
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1 text-xs">
                      <ToneBadge>{TYPE_LABEL[x.type]}</ToneBadge>
                      {x.difficulty && <ToneBadge tone="blue">{DIFFICULTY_LABEL[x.difficulty] ?? x.difficulty}</ToneBadge>}
                      {x.grade && <ToneBadge>Lớp {x.grade}</ToneBadge>}
                      {primary && (
                        <ToneBadge tone="blue" className="h-auto whitespace-normal">
                          {primary.name}
                        </ToneBadge>
                      )}
                      {x.tags.map((t) => (
                        <ToneBadge key={t.id} className="font-normal">
                          #{t.name}
                        </ToneBadge>
                      ))}
                    </div>
                  </div>
                  <Button size="sm" variant={already || other ? "ghost" : "outline"} disabled={already || other} onClick={() => onChoose(x.id)}>
                    {already ? "Đã có trong đề" : other ? "Khác loại" : "Chọn"}
                  </Button>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
}
