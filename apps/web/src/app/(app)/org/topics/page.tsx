"use client";

import { useEffect, useState } from "react";
import { useMe } from "@/app/(app)/AppShell";
import { TopicTree } from "@/components/topics/TopicTree";
import { Empty, PageHeader, Select } from "@/components/ui";
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
        subtitle="Nhấp đúp vào tên để đổi tên. Câu hỏi gắn vào nhánh cuối; thống kê cộng dồn lên các cấp trên."
        actions={
          <Select value={subjectId} onChange={(e) => setSubjectId(e.target.value)} aria-label="Môn học">
            {tax?.subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        }
      />
      {topics && topics.length === 0 && <Empty>Môn này chưa có cây chuyên đề. Thêm mạch kiến thức đầu tiên bên dưới.</Empty>}
      {topics && <TopicTree key={subjectId} topics={topics} subjectId={subjectId} onChange={reload} readOnly={me.role === "student"} />}
    </>
  );
}
