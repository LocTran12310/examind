"use client";

import { use } from "react";
import { ResultView } from "@/components/exams/ResultView";
import { PageHeader } from "@/components/app/PageHeader";
import { useApi } from "@/lib/hooks";
import type { AttemptResult, AttemptView } from "@/lib/types";
import { useMe } from "../../AppShell";

export default function ResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const me = useMe();
  const staff = me.role === "org_admin" || me.role === "teacher";
  const { data, reload, error } = useApi<AttemptResult>(`/attempts/${id}/result`);
  const { data: attempt } = useApi<AttemptView>(staff ? `/attempts/${id}` : null);
  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!data) return null;
  return (
    <>
      <PageHeader title={data.title} description={staff && attempt ? `Bài làm của ${attempt.student.full_name} (${attempt.student.username})` : undefined} />
      <ResultView result={data} staff={staff} onChange={reload} />
    </>
  );
}
