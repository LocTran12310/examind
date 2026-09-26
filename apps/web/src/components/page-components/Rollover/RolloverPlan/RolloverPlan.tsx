"use client";

import type { RolloverClass as PlanClass, RolloverPlan as Plan } from "@/interfaces/school-year.interface";
import { RolloverClassCard } from "../RolloverClassCard/RolloverClassCard";

export interface RolloverPlanProps {
  plan: Plan;
  onChange: (classes: PlanClass[]) => void;
}

/** One folded card per class: target name (editable), and an action per student (school-years AC-09/AC-10). */
export function RolloverPlan({ plan, onChange }: RolloverPlanProps) {
  return (
    <div className="grid gap-4">
      {plan.classes.length === 0 && <p className="text-sm text-muted-foreground">Năm học này chưa có lớp.</p>}
      {plan.classes.map((c, i) => (
        <RolloverClassCard key={c.source_class_id} c={c} onChange={(next) => onChange(plan.classes.map((x, j) => (j === i ? next : x)))} />
      ))}
    </div>
  );
}
