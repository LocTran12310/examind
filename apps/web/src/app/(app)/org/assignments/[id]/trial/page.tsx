"use client";

import { use } from "react";
import { ExamTrialPage } from "@/components/page-components/ExamTrial/ExamTrialPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ExamTrialPage id={id} />;
}
