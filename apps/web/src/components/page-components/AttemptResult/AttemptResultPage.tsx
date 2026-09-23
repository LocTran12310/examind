"use client";

import { BackLink } from "@/components/common/BackLink/BackLink";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { useAttemptResultPage } from "@/hooks/page-hooks/attempt-result/use-attempt-result-page";
import { ResultView } from "./ResultView/ResultView";

export function AttemptResultPage({ id }: { id: string }) {
  const p = useAttemptResultPage(id);
  const back = <BackLink href={p.back.href}>{p.back.label}</BackLink>;
  // a result that cannot be read is exactly when the way out matters
  if (p.error) return <>{back}<p className="text-sm text-destructive">{p.error}</p></>;
  if (!p.result) return null;
  return (
    <>
      {back}
      <PageHeader title={p.result.title} description={p.description} />
      <ResultView result={p.result} staff={p.staff} />
    </>
  );
}
