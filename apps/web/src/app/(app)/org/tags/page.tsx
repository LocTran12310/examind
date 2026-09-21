"use client";

import { TagManager } from "@/components/tags/TagManager";
import { PageHeader } from "@/components/ui";
import { useApi } from "@/lib/hooks";
import type { Tag } from "@/lib/types";

export default function TagsPage() {
  const { data, reload } = useApi<Tag[]>("/tags");
  return (
    <>
      <PageHeader title="Tags" subtitle="Nhãn tự do, gắn nhiều nhãn cho một câu hỏi; bấm vào tag để đổi tên" />
      {data && <TagManager tags={data} onChange={reload} />}
    </>
  );
}
