"use client";

import { ArrowLeft, ArrowRightLeft } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { PageHeader } from "@/components/app/PageHeader";
import { useYear } from "@/components/app/YearContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError } from "@/lib/api";
import { ACTION_LABEL, type Action, type Plan, RolloverPlan, tally } from "./RolloverPlan";

interface Result {
  target_code: string;
  classes_created: string[];
  promote: number;
  retain: number;
  transfer: number;
  graduate: number;
}

export function RolloverWizard({ yearId }: { yearId: string }) {
  const { reload: reloadYears, setYear } = useYear();
  const [target, setTarget] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activate, setActivate] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<Result | null>(null);

  async function load(code?: string) {
    setError(null);
    try {
      const p = await api<Plan>(`/school-years/${yearId}/rollover/preview`, { body: { target_code: code || null } });
      setPlan(p);
      setTarget(p.target_code);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không lập được kế hoạch");
    }
  }
  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [yearId]);

  const counts = plan ? tally(plan.classes) : null;

  async function commit() {
    if (!plan) return;
    setConfirming(false);
    try {
      const body = {
        target_code: plan.target_code,
        activate_target: activate,
        classes: plan.classes.map((c) => ({ source_class_id: c.source_class_id, target_name: c.target_name, students: c.students.map((s) => ({ user_id: s.user_id, action: s.action })) })),
      };
      const r = await api<Result & { target_year_id: string }>(`/school-years/${yearId}/rollover/commit`, { body });
      setResult(r);
      await reloadYears();
      if (activate) setYear(r.target_year_id);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không chuyển được năm học");
    }
  }

  return (
    <>
      <Button variant="ghost" size="sm" asChild className="mb-2">
        <Link href="/org/school-years">
          <ArrowLeft /> Năm học
        </Link>
      </Button>
      <PageHeader title={`Chuyển năm học${plan ? ` ${plan.source_year.code} → ${plan.target_code}` : ""}`} description="Mặc định cả lớp lên lớp (khối cuối: tốt nghiệp). Chỉ cần sửa các trường hợp ngoại lệ." />
      {error && <FormAlert className="mb-4">{error}</FormAlert>}
      {result ? (
        <FormAlert kind="success">
          Đã chuyển sang {result.target_code}: {result.promote} lên lớp, {result.retain} ở lại, {result.transfer} chuyển đi, {result.graduate} tốt nghiệp.
          {result.classes_created.length > 0 && ` Tạo lớp: ${result.classes_created.join(", ")}.`}{" "}
          <Link className="underline" href="/org/classes">
            Xem lớp học
          </Link>
        </FormAlert>
      ) : !plan ? (
        <Skeleton className="h-60" />
      ) : (
        <div className="grid gap-4">
          <Card>
            <CardContent className="flex flex-wrap items-end gap-4">
              <FormField label="Năm học mới" className="w-40">
                <Input value={target} onChange={(e) => setTarget(e.target.value)} onBlur={() => target !== plan.target_code && void load(target)} />
              </FormField>
              <div className="flex flex-wrap gap-3 text-sm" aria-label="Tổng hợp">
                {(Object.keys(ACTION_LABEL) as Action[]).map((a) => (
                  <span key={a}>
                    {ACTION_LABEL[a]}: <strong className="tabular-nums">{counts?.[a] ?? 0}</strong>
                  </span>
                ))}
              </div>
              <div className="ml-auto flex items-center gap-2">
                <Checkbox id="activate" checked={activate} onCheckedChange={(v) => setActivate(v === true)} />
                <Label htmlFor="activate">Đặt {plan.target_code} làm năm đang học (khóa năm cũ)</Label>
              </div>
              <Button onClick={() => setConfirming(true)} disabled={!plan.classes.length}>
                <ArrowRightLeft /> Xác nhận chuyển năm
              </Button>
            </CardContent>
          </Card>
          <RolloverPlan plan={plan} onChange={(classes) => setPlan({ ...plan, classes })} />
        </div>
      )}
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title={`Chuyển ${plan?.source_year.code ?? ""} → ${plan?.target_code ?? ""}?`}
        description={counts ? `${counts.promote} lên lớp, ${counts.retain} ở lại, ${counts.transfer} chuyển đi, ${counts.graduate} tốt nghiệp. Có thể chạy lại để bổ sung; không tạo trùng.` : undefined}
        confirmLabel="Chuyển năm"
        onConfirm={commit}
      />
    </>
  );
}
