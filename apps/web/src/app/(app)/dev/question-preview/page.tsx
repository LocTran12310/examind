"use client";

import { useState } from "react";
import { QuestionView, type QuestionMode } from "@/components/common/QuestionView/QuestionView";
import { Panel } from "@/components/app/Panel";
import { PageHeader } from "@/components/app/PageHeader";
import { OptionSelect } from "@/components/app/OptionSelect";
import { ApiError } from "@/lib/api";
// eslint-disable-next-line no-restricted-imports -- screen moves to a page hook in its own slice
import { useQuestionDemoQuery } from "@/hooks/react-query/use-query-question";

export default function QuestionPreviewPage() {
  const { data, error: failed } = useQuestionDemoQuery();
  const error = failed ? (failed instanceof ApiError ? failed.message : "Không tải được dữ liệu") : null;
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
