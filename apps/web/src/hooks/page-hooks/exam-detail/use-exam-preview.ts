import { useExamQuery } from "@/hooks/react-query/use-query-exam";

/** The whole exam of the preview dialog, fetched only once the dialog opens with an id. */
export function useExamPreview(examId: string | null) {
  const { data } = useExamQuery(examId);
  return { exam: data && data.id === examId ? data : null };
}
