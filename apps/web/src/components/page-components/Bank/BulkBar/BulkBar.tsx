"use client";

import { BookOpen, Check, ChevronDown, Gauge, GraduationCap, Network, Tag as TagIcon, Trash2, X } from "lucide-react";
import Link from "next/link";
import { ConfirmDialog } from "@/components/common/ConfirmDialog/ConfirmDialog";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { Markdown } from "@/components/common/Markdown/Markdown";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { TopicPicker } from "@/components/common/TopicPicker/TopicPicker";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { DIFFICULTY_LABEL } from "@/constants/question.constant";
import { useBulkActions } from "@/hooks/page-hooks/bank/use-bulk-actions";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { Tag } from "@/interfaces/tag.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import type { Topic } from "@/interfaces/topic.interface";

/** How many questions the action will change, worn by the action itself, so a click is never about a
 *  selection the teacher has stopped watching (bulk-safety AC-06). The count stays a badge and the unit is
 *  read out rather than drawn: at 390px the toolbar already wraps. */
function Count({ n }: { n: number }) {
  if (!n) return null;
  return (
    <span className="rounded-sm bg-sidebar-foreground/15 px-1 text-xs tabular-nums">
      <span aria-hidden>{n}</span>
      <span className="sr-only">{n} câu</span>
    </span>
  );
}

/** Bulk actions for the selected questions, rendered inside the table toolbar. "Môn" and "Lớp" make the
 *  "Chưa phân môn" tab actionable (AC-05); a subject the topics contradict is refused whole and the
 *  refusal is shown with the questions in the way (A-04). */
export function BulkActions({
  ids,
  topics,
  subjectId,
  tags,
  taxonomy,
  questions,
  onDone,
  onClear,
}: {
  ids: string[];
  topics: Topic[];
  /** the subject the bank is showing: the picker's numbers are its questions (ADR-01) */
  subjectId?: string | null;
  tags: Tag[];
  taxonomy?: Taxonomy;
  /** the page on screen, so a conflicting question is named by its number rather than by its id */
  questions?: ParsedQuestion[];
  onDone?: () => void;
  onClear: () => void;
}) {
  const b = useBulkActions({ ids, subjectId, onDone, onClear });
  const subjects = taxonomy?.subjects ?? [];
  const grades = taxonomy?.grades ?? [];
  const n = ids.length;
  const questionOf = (questionId: string) => questions?.find((x) => x.id === questionId);
  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <ToolbarButton disabled={b.none}>
            <Gauge /> Mức độ <Count n={n} /> <ChevronDown />
          </ToolbarButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuLabel>Đặt mức độ cho {n} câu</DropdownMenuLabel>
          {Object.entries(DIFFICULTY_LABEL).map(([k, v]) => (
            <DropdownMenuItem key={k} onSelect={() => void b.apply({ difficulty: k }, `Đã đặt mức độ ${v}`)}>
              {v}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <ToolbarButton disabled={b.none || !subjects.length}>
            <BookOpen /> Môn <Count n={n} /> <ChevronDown />
          </ToolbarButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="max-h-72 overflow-y-auto">
          <DropdownMenuLabel>Đổi môn cho {n} câu</DropdownMenuLabel>
          {subjects.map((s) => (
            <DropdownMenuItem key={s.id} onSelect={() => void b.apply({ subject_id: s.id }, `Đã đặt môn ${s.name}`)}>
              {s.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <ToolbarButton disabled={b.none || !grades.length}>
            <GraduationCap /> Lớp <Count n={n} /> <ChevronDown />
          </ToolbarButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="max-h-72 overflow-y-auto">
          <DropdownMenuLabel>Đặt lớp cho {n} câu</DropdownMenuLabel>
          {grades.map((g) => (
            <DropdownMenuItem key={g.id} onSelect={() => void b.apply({ grade: g.level }, `Đã đặt ${g.name}`)}>
              {g.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <ToolbarButton disabled={b.none} onClick={() => b.setPicking(true)}>
        <Network /> Chuyên đề <Count n={n} />
      </ToolbarButton>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <ToolbarButton disabled={b.none || !tags.length}>
            <TagIcon /> Thêm tag <Count n={n} /> <ChevronDown />
          </ToolbarButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="max-h-72 overflow-y-auto">
          <DropdownMenuLabel>Thêm tag cho {n} câu</DropdownMenuLabel>
          {tags.map((t) => (
            <DropdownMenuItem key={t.id} onSelect={() => void b.apply({ add_tag_ids: [t.id] }, `Đã thêm tag ${t.name}`)}>
              {t.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <ToolbarButton disabled={b.none} onClick={() => void b.apply({ status: "approved" }, "Đã duyệt")}>
        <Check /> Duyệt <Count n={n} />
      </ToolbarButton>
      <ToolbarButton disabled={b.none} onClick={() => void b.apply({ status: "rejected" }, "Đã loại")}>
        <X /> Loại <Count n={n} />
      </ToolbarButton>
      <ToolbarButton disabled={b.none} onClick={() => b.setConfirming(true)}>
        <Trash2 /> Xóa <Count n={n} />
      </ToolbarButton>
      <ConfirmDialog
        open={b.confirming}
        onOpenChange={b.setConfirming}
        destructive
        title={`Xóa vĩnh viễn ${n} câu hỏi?`}
        description="Câu đang dùng trong đề thi sẽ không bị xóa."
        confirmLabel="Xóa"
        onConfirm={async () => {
          b.setConfirming(false);
          await b.remove();
        }}
      />
      <FormDialog open={b.picking} title={`Đặt chuyên đề cho ${n} câu`} onOpenChange={b.setPicking}>
        <TopicPicker
          topics={topics}
          counts={b.topicCounts}
          onPick={(t) => {
            b.setPicking(false);
            void b.apply({ primary_topic_id: t.id }, `Đã đặt chuyên đề ${t.name}`);
          }}
          onClose={() => b.setPicking(false)}
        />
      </FormDialog>
      <FormDialog open={!!b.conflict} title="Chưa đổi được môn" onOpenChange={(o) => !o && b.setConflict(null)}>
        <div className="grid gap-3" data-testid="subject-conflict">
          <FormAlert kind="warning">{b.conflict?.message}</FormAlert>
          {!!b.conflict?.conflicts.length && (
            <ul className="grid gap-1 text-sm">
              {b.conflict.conflicts.map((c) => {
                const q = questionOf(c.question_id);
                return (
                  <li key={c.question_id} className="rounded-md border px-2 py-1">
                    <Link href={`/org/bank/${c.question_id}`} className="font-medium hover:text-primary">
                      {q?.number ? `Câu ${q.number}` : `Câu ${c.question_id.slice(0, 8)}`}
                    </Link>
                    <span className="text-muted-foreground"> · chuyên đề {c.topic_name}</span>
                    {/* question numbers repeat from one paper to the next: the stem says which câu this is */}
                    {q && (
                      <div className="max-h-14 overflow-hidden text-xs text-muted-foreground">
                        <Markdown>{q.stem}</Markdown>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
          <p className="text-sm text-muted-foreground">
            Không câu nào bị đổi. Mở từng câu ở trên, bỏ hoặc đổi chuyên đề sang môn mới, rồi đặt lại môn cho cả nhóm.
          </p>
        </div>
      </FormDialog>
    </>
  );
}
