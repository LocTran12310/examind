"use client";

import { BackLink } from "@/components/common/BackLink/BackLink";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { Panel } from "@/components/common/Panel/Panel";
import { QuestionView, type QuestionMode } from "@/components/common/QuestionView/QuestionView";
import { useQuestionPreviewPage } from "@/hooks/page-hooks/question-preview/use-question-preview-page";

export function QuestionPreviewPage() {
  const { data, error, mode, setMode, selected, setSelected } = useQuestionPreviewPage();
  return (
    <>
      <BackLink href="/org/bank">Ngân hàng câu hỏi</BackLink>
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
