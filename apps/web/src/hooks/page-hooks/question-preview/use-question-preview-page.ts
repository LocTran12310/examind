import { useState } from "react";
import type { QuestionMode } from "@/components/common/QuestionView/QuestionView";
import { useQuestionDemoQuery } from "@/hooks/react-query/use-query-question";
import { ApiError } from "@/lib/common/http";

/** The demo question in each QuestionView mode (formulas, pictures, solution). */
export function useQuestionPreviewPage() {
  const { data, error: failed } = useQuestionDemoQuery();
  const [mode, setMode] = useState<QuestionMode>("review");
  const [selected, setSelected] = useState<string | null>(null);
  return {
    data,
    error: failed ? (failed instanceof ApiError ? failed.message : "Không tải được dữ liệu") : null,
    mode,
    setMode,
    selected,
    setSelected,
  };
}
