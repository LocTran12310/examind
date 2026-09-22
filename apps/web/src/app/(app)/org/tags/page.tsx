"use client";

import { TagManager } from "@/components/tags/TagManager";
import { PageHeader } from "@/components/app/PageHeader";
import { useApi } from "@/lib/hooks";
import type { Tag } from "@/lib/types";

export default function TagsPage() {
  const { data, reload } = useApi<Tag[]>("/tags");
  return (
    <>
      <PageHeader title="Tags" description="Nhãn tự do, gắn nhiều nhãn cho một câu hỏi; bấm vào tag để đổi tên" />
      {data && <TagManager tags={data} onChange={reload} />}
    </>
  );
}
