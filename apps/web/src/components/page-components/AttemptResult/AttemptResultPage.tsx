"use client";

import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { useAttemptResultPage } from "@/hooks/page-hooks/attempt-result/use-attempt-result-page";
import { ResultView } from "./ResultView/ResultView";

export function AttemptResultPage({ id }: { id: string }) {
  const p = useAttemptResultPage(id);
  if (p.error) return <p className="text-sm text-destructive">{p.error}</p>;
  if (!p.result) return null;
  return (
    <>
      <PageHeader title={p.result.title} description={p.description} />
      <ResultView result={p.result} staff={p.staff} />
    </>
  );
}
