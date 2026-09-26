import { ROLLOVER_ACTION_LABEL } from "@/constants/school-year.constant";
import type { RolloverAction, RolloverClass, RolloverPlan, RolloverStudent } from "@/interfaces/school-year.interface";
import type { CommitRolloverBody } from "@/dtos/school-year.dto";

/** How many of these students get each action. */
function countActions(students: RolloverStudent[]): Record<RolloverAction, number> {
  const out: Record<RolloverAction, number> = { promote: 0, retain: 0, transfer: 0, graduate: 0 };
  for (const s of students) out[s.action] += 1;
  return out;
}

/** How many students get each action. */
export function tally(classes: RolloverClass[]): Record<RolloverAction, number> {
  return countActions(classes.flatMap((c) => c.students));
}

/** The actions of one class in one line ("Lên lớp 23 · Ở lại lớp 2"): a folded class still has to read as a plan. */
export function actionSummary(students: RolloverStudent[]): string {
  const n = countActions(students);
  return (Object.keys(ROLLOVER_ACTION_LABEL) as RolloverAction[]).filter((a) => n[a] > 0).map((a) => `${ROLLOVER_ACTION_LABEL[a]} ${n[a]}`).join(" · ");
}

/** The (edited) plan as the commit body. */
export function commitBody(plan: RolloverPlan, activate: boolean): CommitRolloverBody {
  return {
    target_code: plan.target_code,
    activate_target: activate,
    classes: plan.classes.map((c) => ({ source_class_id: c.source_class_id, target_name: c.target_name, students: c.students.map((s) => ({ user_id: s.user_id, action: s.action })) })),
  };
}
