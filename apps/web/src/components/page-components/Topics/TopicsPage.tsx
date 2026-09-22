"use client";

import { EmptyState } from "@/components/app/EmptyState";
import { OptionSelect } from "@/components/app/OptionSelect";
import { PageHeader } from "@/components/app/PageHeader";
import { useTopicsPage } from "@/hooks/page-hooks/topics/use-topics-page";
import { TopicTree } from "./TopicTree/TopicTree";

export function TopicsPage() {
  const p = useTopicsPage();
  return (
    <>
      <PageHeader
        title="Cây chuyên đề"
        description="Nhấp đúp vào tên để đổi tên. Câu hỏi gắn vào nhánh cuối; thống kê cộng dồn lên các cấp trên."
        actions={<OptionSelect className="w-48" value={p.subjectId} onValueChange={p.setSubjectId} aria-label="Môn học" options={p.subjectOptions} />}
      />
      {p.topics && p.topics.length === 0 && <EmptyState>Môn này chưa có cây chuyên đề. Thêm mạch kiến thức đầu tiên bên dưới.</EmptyState>}
      {p.topics && <TopicTree key={p.subjectId} topics={p.topics} subjectId={p.subjectId} readOnly={p.readOnly} />}
    </>
  );
}
