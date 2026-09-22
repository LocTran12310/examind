"use client";

import { ArrowLeft, ArrowRightLeft } from "lucide-react";
import Link from "next/link";
import { ConfirmDialog } from "@/components/common/ConfirmDialog/ConfirmDialog";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormField } from "@/components/common/FormField/FormField";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ROLLOVER_ACTION_LABEL as ACTION_LABEL } from "@/constants/school-year.constant";
import { useRollover } from "@/hooks/page-hooks/rollover/use-rollover";
import type { RolloverAction as Action } from "@/interfaces/school-year.interface";
import { RolloverPlan } from "./RolloverPlan/RolloverPlan";

/** Chuyển năm học of one year (school-years US-05). */
export function RolloverPage({ yearId }: { yearId: string }) {
  const r = useRollover(yearId);
  const plan = r.plan;
  return (
    <>
      <Button variant="ghost" size="sm" asChild className="mb-2">
        <Link href="/org/school-years">
          <ArrowLeft /> Năm học
        </Link>
      </Button>
      <PageHeader title={`Chuyển năm học${plan ? ` ${plan.source_year.code} → ${plan.target_code}` : ""}`} description="Mặc định cả lớp lên lớp (khối cuối: tốt nghiệp). Chỉ cần sửa các trường hợp ngoại lệ." />
      {r.error && <FormAlert className="mb-4">{r.error}</FormAlert>}
      {r.result ? (
        <FormAlert kind="success">
          Đã chuyển sang {r.result.target_code}: {r.result.promote} lên lớp, {r.result.retain} ở lại, {r.result.transfer} chuyển đi, {r.result.graduate} tốt nghiệp.
          {r.result.classes_created.length > 0 && ` Tạo lớp: ${r.result.classes_created.join(", ")}.`}{" "}
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
                <Input value={r.target} onChange={(e) => r.setTarget(e.target.value)} onBlur={r.replan} />
              </FormField>
              <div className="flex flex-wrap gap-3 text-sm" aria-label="Tổng hợp">
                {(Object.keys(ACTION_LABEL) as Action[]).map((a) => (
                  <span key={a}>
                    {ACTION_LABEL[a]}: <strong className="tabular-nums">{r.counts?.[a] ?? 0}</strong>
                  </span>
                ))}
              </div>
              <div className="ml-auto flex items-center gap-2">
                <Checkbox id="activate" checked={r.activate} onCheckedChange={(v) => r.setActivate(v === true)} />
                <Label htmlFor="activate">Đặt {plan.target_code} làm năm đang học (khóa năm cũ)</Label>
              </div>
              <Button onClick={() => r.setConfirming(true)} disabled={!plan.classes.length}>
                <ArrowRightLeft /> Xác nhận chuyển năm
              </Button>
            </CardContent>
          </Card>
          <RolloverPlan plan={plan} onChange={r.setClasses} />
        </div>
      )}
      <ConfirmDialog
        open={r.confirming}
        onOpenChange={r.setConfirming}
        title={`Chuyển ${plan?.source_year.code ?? ""} → ${plan?.target_code ?? ""}?`}
        description={r.counts ? `${r.counts.promote} lên lớp, ${r.counts.retain} ở lại, ${r.counts.transfer} chuyển đi, ${r.counts.graduate} tốt nghiệp. Có thể chạy lại để bổ sung; không tạo trùng.` : undefined}
        confirmLabel="Chuyển năm"
        onConfirm={r.commit}
      />
    </>
  );
}
