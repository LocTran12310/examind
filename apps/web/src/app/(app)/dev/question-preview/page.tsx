"use client";

import { useState } from "react";
import { QuestionView, type QuestionMode } from "@/components/question/QuestionView";
import { Panel } from "@/components/app/Panel";
import { PageHeader } from "@/components/app/PageHeader";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { useApi } from "@/lib/hooks";
import type { Question } from "@/lib/types";

export default function QuestionPreviewPage() {
  const { data, error } = useApi<Question>("/questions/demo");
  const [mode, setMode] = useState<QuestionMode>("review");
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <>
      <PageHeader
        title="Xem trước câu hỏi"
        description="Câu mẫu dùng để kiểm tra hiển thị công thức, hình và lời giải"
        actions={
          <NativeSelect value={mode} onChange={(e) => setMode(e.target.value as QuestionMode)} aria-label="Chế độ">
            <NativeSelectOption value="review">Chế độ duyệt (hiện đáp án)</NativeSelectOption>
            <NativeSelectOption value="exam">Chế độ làm bài (ẩn đáp án)</NativeSelectOption>
            <NativeSelectOption value="result">Chế độ kết quả</NativeSelectOption>
          </NativeSelect>
        }
      />
      {error && <p className="text-sm text-destructive">{error}</p>}
      {data && (
        <Panel className="max-w-3xl">
          <QuestionView key={mode} question={data} mode={mode} number={1} selected={selected} onSelect={mode === "exam" ? setSelected : undefined} />
        </Panel>
      )}
    </>
  );
}
