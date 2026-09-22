import { useState } from "react";
import { useSaveGradeMutation, useSaveLevelMutation } from "@/hooks/react-query/use-query-structure";
import type { GradeRow, SchoolLevel } from "@/interfaces/structure.interface";
import { formErrors } from "@/lib/common/form-errors";

/** Create or edit a cấp học; `onDone` after the server accepted it. */
export function useLevelForm(level: SchoolLevel | undefined, onDone: () => void) {
  const [v, setV] = useState({ code: level?.code ?? "", name: level?.name ?? "", grade_from: String(level?.grade_from ?? ""), grade_to: String(level?.grade_to ?? "") });
  const save = useSaveLevelMutation();
  const { fields, message } = formErrors(save.error);
  return {
    v,
    set: (k: keyof typeof v) => (e: React.ChangeEvent<HTMLInputElement>) => setV({ ...v, [k]: e.target.value }),
    busy: save.isPending,
    fields,
    message,
    submit: () =>
      save.mutate(
        { id: level?.id, body: { code: v.code, name: v.name, grade_from: Number(v.grade_from), grade_to: Number(v.grade_to) } },
        { onSuccess: onDone },
      ),
  };
}

/** Create or edit a khối of `levelId`. */
export function useGradeForm(grade: GradeRow | undefined, levelId: string, onDone: () => void) {
  const [level, setLevel] = useState(String(grade?.level ?? ""));
  const [name, setName] = useState(grade?.name ?? "");
  const save = useSaveGradeMutation();
  const { fields, message } = formErrors(save.error);
  return {
    level,
    setLevel,
    name,
    setName,
    busy: save.isPending,
    fields,
    message,
    submit: () => save.mutate({ id: grade?.id, body: { level: Number(level), name: name || null, school_level_id: levelId } }, { onSuccess: onDone }),
  };
}
