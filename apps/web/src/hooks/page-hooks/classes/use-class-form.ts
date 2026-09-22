import { useState } from "react";
import type { ClassBody } from "@/dtos/class.dto";
import { useYear } from "@/hooks/common/use-year";
import { useSaveClassMutation } from "@/hooks/react-query/use-query-class";
import type { SchoolClass } from "@/interfaces/class.interface";
import { formErrors } from "@/lib/common/form-errors";
import { currentSchoolYear } from "@/lib/page-libs/classes/school-year";

/** Create (no `klass`) or edit a class; a new class goes to the year chosen in the header. */
export function useClassForm(klass: SchoolClass | undefined, gradeId: string | undefined, onDone: () => void) {
  const { years, year: selected } = useYear();
  const [name, setName] = useState(klass?.name ?? "");
  const [grade, setGrade] = useState(klass?.grade_id ?? gradeId ?? "");
  const [yearId, setYearId] = useState(klass?.school_year_id ?? selected?.id ?? "");
  const save = useSaveClassMutation();
  const { fields, message } = formErrors(save.error);
  return {
    name,
    setName,
    grade,
    setGrade,
    yearId,
    setYearId,
    yearOptions: years.map((y) => ({ value: y.id, label: y.code })),
    fallbackYear: currentSchoolYear(),
    busy: save.isPending,
    fields,
    message,
    submit: () => {
      const body: ClassBody = yearId ? { name, grade_id: grade || null, school_year_id: yearId } : { name, grade_id: grade || null, school_year: currentSchoolYear() };
      save.mutate({ id: klass?.id, body }, { onSuccess: onDone });
    },
  };
}
