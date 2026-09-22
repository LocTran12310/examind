"use client";

import { useRouter } from "next/navigation";
import { use, useEffect } from "react";
import { ExamRunner } from "@/components/exams/ExamRunner";
import { useApi } from "@/lib/hooks";
import type { AttemptView } from "@/lib/types";

export default function ExamPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { data, error } = useApi<AttemptView>(`/attempts/${id}`);
  useEffect(() => {
    if (data && data.status !== "in_progress") router.replace(`/results/${id}`);
  }, [data, id, router]);
  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!data || data.status !== "in_progress") return null;
  return <ExamRunner view={data} onFinished={() => router.replace(`/results/${id}`)} />;
}
