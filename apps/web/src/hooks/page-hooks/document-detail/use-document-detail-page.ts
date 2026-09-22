import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { DEFAULT_THRESHOLD, PROCESSING_POLL_MS } from "@/constants/document.constant";
import { useAiModelOptionsQuery } from "@/hooks/react-query/use-query-ai-model";
import { documentFileUrl, useCreateExamFromDocumentMutation, useDocumentQuery, useDocumentQuestionsQuery, useReparseDocumentMutation } from "@/hooks/react-query/use-query-document";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import type { ProcessingConfig, SourceDocument } from "@/interfaces/document.interface";
import { formErrors } from "@/lib/common/form-errors";
import { ApiError } from "@/lib/common/http";

const processing = (d?: SourceDocument) => d?.status === "queued" || d?.status === "processing";

/** One uploaded document: polls while it is processed, its parsed questions, "Tách lại" and "Tạo đề từ tài liệu". */
export function useDocumentDetailPage(id: string) {
  const dup = useSearchParams().get("dup");
  const router = useRouter();
  const { data: doc } = useDocumentQuery(id, (d) => (processing(d) ? PROCESSING_POLL_MS : false));
  const { data: taxonomy } = useTaxonomyQuery();
  const parsed = doc?.status === "parsed";
  const { data: questions } = useDocumentQuestionsQuery(id, parsed);
  const [onlyIssues, setOnlyIssues] = useState(false);
  const [reparseConfig, setReparseConfig] = useState<ProcessingConfig | null>(null);
  const { data: models } = useAiModelOptionsQuery(!!reparseConfig);
  const reparse = useReparseDocumentMutation();
  const makeExam = useCreateExamFromDocumentMutation();

  const threshold = doc?.processing_config?.threshold ?? DEFAULT_THRESHOLD;
  const all = questions ?? [];
  const low = all.filter((q) => (q.confidence ?? 0) < threshold);
  return {
    doc,
    taxonomy,
    duplicate: !!dup,
    fileUrl: documentFileUrl(id),
    busy: processing(doc),
    parsed,
    questions,
    shown: onlyIssues ? low : all,
    low: low.length,
    threshold,
    warnings: doc?.log.find((l) => l.step === "warnings")?.items ?? [],
    onlyIssues,
    setOnlyIssues,
    models: models ?? [],
    reparseConfig,
    setReparseConfig,
    openReparse: () => {
      reparse.reset();
      setReparseConfig(doc?.processing_config ?? null);
    },
    reparseError: formErrors(reparse.error).message,
    submitReparse: () => {
      if (!reparseConfig) return;
      reparse.mutate({ id, body: { config: reparseConfig } }, { onSuccess: () => setReparseConfig(null) });
    },
    making: makeExam.isPending,
    createExam: () =>
      makeExam.mutate(
        { id, body: {} },
        {
          onSuccess: (r) => {
            toast.success(`Đã tạo đề thi với ${r.added} câu` + (r.skipped ? ` — bỏ qua ${r.skipped} câu chưa duyệt` : ""));
            router.push(`/org/exams/${r.exam_id}`);
          },
          onError: (e) => toast.error(e instanceof ApiError ? e.message : "Không tạo được đề"),
        },
      ),
  };
}
