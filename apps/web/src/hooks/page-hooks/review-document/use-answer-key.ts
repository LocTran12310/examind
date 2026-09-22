import { useState } from "react";
import { useAnswerKeyMutation } from "@/hooks/react-query/use-query-review";
import type { AnswerKeyResult } from "@/interfaces/review.interface";
import { ApiError } from "@/lib/common/http";

/** "Dán bảng đáp án": the pasted text and the summary of what was applied. */
export function useAnswerKey(docId: string) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<AnswerKeyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const apply = useAnswerKeyMutation(docId);
  return {
    text,
    setText,
    result,
    error,
    submit: async () => {
      setError(null);
      try {
        setResult(await apply.mutateAsync(text));
      } catch (e) {
        setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
      }
    },
  };
}
