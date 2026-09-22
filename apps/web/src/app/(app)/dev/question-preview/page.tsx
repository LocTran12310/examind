"use client";

import { useState } from "react";
import { QuestionView, type QuestionMode } from "@/components/question/QuestionView";
import { Panel } from "@/components/app/Panel";
import { PageHeader } from "@/components/app/PageHeader";
import { OptionSelect } from "@/components/app/OptionSelect";
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
          <OptionSelect
            className="w-64"
            value={mode}
            onValueChange={(v) => setMode(v as QuestionMode)}
            aria-label="Chế độ"
            options={[
              { value: "review", label: "Chế độ duyệt (hiện đáp án)" },
              { value: "exam", label: "Chế độ làm bài (ẩn đáp án)" },
              { value: "result", label: "Chế độ kết quả" },
            ]}
          />
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
