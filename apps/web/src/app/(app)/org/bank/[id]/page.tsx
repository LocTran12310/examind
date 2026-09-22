"use client";

import { use } from "react";
import { QuestionDetailPage } from "@/components/page-components/QuestionDetail/QuestionDetailPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <QuestionDetailPage id={id} />;
}
