"use client";

import Link from "next/link";
import { use, useState } from "react";
import { AssignDialog } from "@/components/exams/AssignDialog";
import { BlueprintEditor } from "@/components/exams/BlueprintEditor";
import { ExamQuestions, moved } from "@/components/exams/ExamQuestions";
import { Markdown } from "@/components/question/Markdown";
import { QuestionView } from "@/components/question/QuestionView";
import { Alert, Button, Card, Input, Modal, PageHeader } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { qs, useApi } from "@/lib/hooks";
import { fmt } from "@/lib/dates";
import { TYPE_LABEL, type Assignment, type BlueprintRow, type Exam, type Page, type ParsedQuestion, type QuestionType, type SchoolClass, type Tag, type Topic } from "@/lib/types";

export default function ExamBuilderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: exam, setData } = useApi<Exam>(`/exams/${id}`);
  const { data: topics } = useApi<Topic[]>("/topics");
  const { data: tags } = useApi<Tag[]>("/tags");
  const [shortfalls, setShortfalls] = useState<{ row: number; missing: number }[]>([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const { data: found } = useApi<Page<ParsedQuestion>>(query ? `/questions${qs({ q: query, page_size: 10 })}` : null);
  const [preview, setPreview] = useState<null | "exam" | "review">(null);
  const [error, setError] = useState<string | null>(null);
  const [assigning, setAssigning] = useState(false);
  const { data: classes } = useApi<SchoolClass[]>("/classes");
  const { data: assigned, reload: reloadAssigned } = useApi<Assignment[]>(`/assignments?exam_id=${id}`);

  async function run(fn: () => Promise<Exam | { exam: Exam; shortfalls: { row: number; missing: number }[] }>) {
    setError(null);
    try {
      const r = await fn();
      if ("exam" in r) {
        setData(r.exam);
        setShortfalls(r.shortfalls);
      } else setData(r);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  if (!exam || !topics || !tags) return null;
  const ids = exam.questions.map((q) => q.id);
  const inExam = new Set(ids);

  return (
    <>
      <Link href="/org/exams" className="text-sm text-gray-500 hover:underline">
        ← Đề thi
      </Link>
      <PageHeader
        title={exam.title}
        subtitle={`${exam.question_count} câu · tổng ${exam.total_points} điểm (quy về thang ${exam.settings.scale_to})`}
        actions={
          <>
            <Button onClick={() => setPreview("exam")} disabled={!exam.question_count}>
              Xem trước
            </Button>
            <Button variant="primary" onClick={() => setAssigning(true)} disabled={!exam.question_count}>
              Giao bài
            </Button>
          </>
        }
      />
      {error && <div className="mb-3"><Alert>{error}</Alert></div>}
      <div className="grid gap-6 xl:grid-cols-[3fr_2fr]">
        <div className="space-y-4">
          <Card>
            <h2 className="mb-3 font-medium">Ma trận đề</h2>
            <BlueprintEditor
              initial={exam.blueprint}
              topics={topics}
              tags={tags}
              shortfalls={shortfalls}
              onGenerate={(rows: BlueprintRow[]) => run(() => api(`/exams/${id}/blueprint`, { body: { rows } }))}
            />
          </Card>
          <Card>
            <h2 className="mb-2 font-medium">Câu hỏi trong đề</h2>
            {exam.questions.length === 0 ? (
              <p className="text-sm text-gray-500">Chưa có câu nào — tạo theo ma trận hoặc thêm từ ngân hàng.</p>
            ) : (
              <ExamQuestions
                questions={exam.questions}
                onMove={(qid, d) => run(() => api(`/exams/${id}/order`, { method: "PUT", body: { question_ids: moved(ids, qid, d) } }))}
                onSwap={(qid) => run(() => api(`/exams/${id}/questions/${qid}/swap`, { method: "POST" }))}
                onRemove={(qid) => run(() => api(`/exams/${id}/questions/${qid}`, { method: "DELETE" }))}
                onPoints={(qid, points) => run(() => api(`/exams/${id}/questions/${qid}`, { method: "PATCH", body: { points } }))}
              />
            )}
          </Card>
        </div>
        <div className="space-y-4">
          {assigned && assigned.length > 0 && (
            <Card>
              <h2 className="mb-2 font-medium">Đã giao</h2>
              <ul className="divide-y divide-gray-100 text-sm" data-testid="assigned">
                {assigned.map((a) => (
                  <li key={a.id} className="flex items-center justify-between py-2">
                    <span>
                      <Link href={`/org/assignments/${a.id}`} className="font-medium text-brand-700 hover:underline">
                        {a.title}
                      </Link>
                      <span className="block text-xs text-gray-500">
                        {a.classes.join(", ")} · {fmt(a.open_at)} → {fmt(a.close_at)}
                      </span>
                    </span>
                    <span className="text-xs text-gray-600">
                      {a.submitted}/{a.students} đã nộp
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
          <Card>
            <h2 className="mb-2 font-medium">Điểm mặc định theo loại câu</h2>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {(Object.keys(TYPE_LABEL) as QuestionType[]).map((t) => (
                <label key={t} className="flex items-center justify-between gap-2">
                  {TYPE_LABEL[t]}
                  <Input
                    aria-label={`Điểm ${TYPE_LABEL[t]}`}
                    type="number"
                    step="0.05"
                    min={0.05}
                    className="h-8 w-20"
                    defaultValue={exam.settings.points_by_type[t]}
                    onBlur={(e) =>
                      Number(e.target.value) !== exam.settings.points_by_type[t] &&
                      run(() => api(`/exams/${id}`, { method: "PATCH", body: { settings: { points_by_type: { [t]: Number(e.target.value) } } } }))
                    }
                  />
                </label>
              ))}
            </div>
          </Card>
          <Card>
            <h2 className="mb-2 font-medium">Thêm từ ngân hàng</h2>
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                setQuery(search);
              }}
            >
              <Input placeholder="Tìm câu hỏi…" value={search} onChange={(e) => setSearch(e.target.value)} />
              <Button type="submit">Tìm</Button>
            </form>
            <ul className="mt-2 divide-y divide-gray-100 text-sm" data-testid="bank-results">
              {found?.items.map((q) => (
                <li key={q.id} className="flex items-start gap-2 py-2">
                  <div className="line-clamp-2 min-w-0 flex-1">
                    <Markdown>{q.stem}</Markdown>
                  </div>
                  <Button size="sm" disabled={inExam.has(q.id)} onClick={() => run(() => api(`/exams/${id}/questions`, { body: { question_ids: [q.id] } }))}>
                    {inExam.has(q.id) ? "Đã có" : "Thêm"}
                  </Button>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
      <Modal open={assigning} title="Giao bài" wide onClose={() => setAssigning(false)}>
        {assigning && (
          <AssignDialog
            examId={id}
            title={exam.title}
            classes={classes ?? []}
            onDone={() => {
              setAssigning(false);
              void reloadAssigned();
            }}
          />
        )}
      </Modal>
      <Modal open={!!preview} title="Xem trước đề" wide onClose={() => setPreview(null)}>
        <label className="mb-4 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={preview === "review"} onChange={(e) => setPreview(e.target.checked ? "review" : "exam")} /> Hiện đáp án và lời giải
        </label>
        <div className="max-h-[70vh] space-y-6 overflow-y-auto" data-testid="exam-preview">
          {exam.questions.map((q) => (
            <QuestionView key={q.id} question={q} mode={preview === "review" ? "review" : "exam"} number={q.position} />
          ))}
        </div>
      </Modal>
    </>
  );
}
