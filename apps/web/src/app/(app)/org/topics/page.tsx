"use client";

import { useEffect, useState } from "react";
import { useMe } from "@/app/(app)/AppShell";
import { TopicTree } from "@/components/topics/TopicTree";
import { EmptyState } from "@/components/app/EmptyState";
import { PageHeader } from "@/components/app/PageHeader";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { qs, useApi } from "@/lib/hooks";
import type { Taxonomy, Topic } from "@/lib/types";

export default function TopicsPage() {
  const me = useMe();
  const { data: tax } = useApi<Taxonomy>("/taxonomy");
  const [subjectId, setSubjectId] = useState("");
  useEffect(() => {
    if (!subjectId && tax?.subjects.length) setSubjectId((tax.subjects.find((s) => s.code === "toan") ?? tax.subjects[0]).id);
  }, [tax, subjectId]);
  const { data: topics, reload } = useApi<Topic[]>(subjectId ? `/topics${qs({ subject_id: subjectId })}` : null);
  return (
    <>
      <PageHeader
        title="Cây chuyên đề"
        description="Nhấp đúp vào tên để đổi tên. Câu hỏi gắn vào nhánh cuối; thống kê cộng dồn lên các cấp trên."
        actions={
          <NativeSelect value={subjectId} onChange={(e) => setSubjectId(e.target.value)} aria-label="Môn học">
            {tax?.subjects.map((s) => (
              <NativeSelectOption key={s.id} value={s.id}>
                {s.name}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        }
      />
      {topics && topics.length === 0 && <EmptyState>Môn này chưa có cây chuyên đề. Thêm mạch kiến thức đầu tiên bên dưới.</EmptyState>}
      {topics && <TopicTree key={subjectId} topics={topics} subjectId={subjectId} onChange={reload} readOnly={me.role === "student"} />}
    </>
  );
}
