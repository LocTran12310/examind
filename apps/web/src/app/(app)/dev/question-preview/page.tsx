"use client";

import { useState } from "react";
import { QuestionView, type QuestionMode } from "@/components/question/QuestionView";
import { Card, PageHeader, Select } from "@/components/ui";
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
        subtitle="Câu mẫu dùng để kiểm tra hiển thị công thức, hình và lời giải"
        actions={
          <Select value={mode} onChange={(e) => setMode(e.target.value as QuestionMode)} aria-label="Chế độ">
            <option value="review">Chế độ duyệt (hiện đáp án)</option>
            <option value="exam">Chế độ làm bài (ẩn đáp án)</option>
            <option value="result">Chế độ kết quả</option>
          </Select>
        }
      />
      {error && <p className="text-sm text-red-700">{error}</p>}
      {data && (
        <Card className="max-w-3xl">
          <QuestionView key={mode} question={data} mode={mode} number={1} selected={selected} onSelect={mode === "exam" ? setSelected : undefined} />
        </Card>
      )}
    </>
  );
}
