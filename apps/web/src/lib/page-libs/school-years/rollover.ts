import type { RolloverAction, RolloverClass, RolloverPlan } from "@/interfaces/school-year.interface";
import type { CommitRolloverBody } from "@/dtos/school-year.dto";

/** How many students get each action. */
export function tally(classes: RolloverClass[]): Record<RolloverAction, number> {
  const out: Record<RolloverAction, number> = { promote: 0, retain: 0, transfer: 0, graduate: 0 };
  for (const c of classes) for (const s of c.students) out[s.action] += 1;
  return out;
}

/** The (edited) plan as the commit body. */
export function commitBody(plan: RolloverPlan, activate: boolean): CommitRolloverBody {
  return {
    target_code: plan.target_code,
    activate_target: activate,
    classes: plan.classes.map((c) => ({ source_class_id: c.source_class_id, target_name: c.target_name, students: c.students.map((s) => ({ user_id: s.user_id, action: s.action })) })),
  };
}
