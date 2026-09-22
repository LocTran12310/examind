import { useEffect, useState } from "react";
import { useYear } from "@/hooks/common/use-year";
import { useCommitRolloverMutation, useRolloverPreviewQuery } from "@/hooks/react-query/use-query-school-year";
import type { RolloverClass, RolloverPlan, RolloverResult } from "@/interfaces/school-year.interface";
import { ApiError } from "@/lib/common/http";
import { commitBody, tally } from "@/lib/page-libs/school-years/rollover";

const message = (e: unknown, fallback: string) => (e instanceof ApiError ? e.message : fallback);

/** Chuyển năm học: the proposed plan (another target code re-plans), the exceptions I edit, then the commit. */
export function useRollover(yearId: string) {
  const { setYear } = useYear();
  const [code, setCode] = useState<string | null>(null);
  const preview = useRolloverPreviewQuery(yearId, code);
  const commitMutation = useCommitRolloverMutation(yearId);
  const [target, setTarget] = useState("");
  const [plan, setPlan] = useState<RolloverPlan | null>(null);
  const [activate, setActivate] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<RolloverResult | null>(null);
  useEffect(() => {
    if (!preview.data) return;
    setPlan(preview.data);
    setTarget(preview.data.target_code);
  }, [preview.data]);
  const error = commitMutation.error ? message(commitMutation.error, "Không chuyển được năm học") : preview.error ? message(preview.error, "Không lập được kế hoạch") : null;
  return {
    plan,
    target,
    setTarget,
    replan: () => plan && target !== plan.target_code && setCode(target || null),
    setClasses: (classes: RolloverClass[]) => plan && setPlan({ ...plan, classes }),
    counts: plan ? tally(plan.classes) : null,
    activate,
    setActivate,
    confirming,
    setConfirming,
    result,
    error,
    commit: async () => {
      if (!plan) return;
      setConfirming(false);
      try {
        const r = await commitMutation.mutateAsync(commitBody(plan, activate));
        setResult(r);
        if (activate) setYear(r.target_year_id);
      } catch {
        // shown through `error`
      }
    },
  };
}
