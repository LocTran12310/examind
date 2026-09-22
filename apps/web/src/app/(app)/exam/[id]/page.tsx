"use client";

import { use } from "react";
import { ExamRunnerPage } from "@/components/page-components/ExamRunner/ExamRunnerPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ExamRunnerPage id={id} />;
}
