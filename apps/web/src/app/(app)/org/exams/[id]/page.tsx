"use client";

import { use } from "react";
import { ExamDetailPage } from "@/components/page-components/ExamDetail/ExamDetailPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ExamDetailPage id={id} />;
}
