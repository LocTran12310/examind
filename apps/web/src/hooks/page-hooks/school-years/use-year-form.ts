import { useState } from "react";
import { useSaveSchoolYearMutation } from "@/hooks/react-query/use-query-school-year";
import type { SchoolYear } from "@/interfaces/school-year.interface";
import { formErrors } from "@/lib/common/form-errors";

/** Create (code, default dates) or edit a year and its HK1/HK2 dates. */
export function useYearForm(year: SchoolYear | undefined, suggest: string | undefined, onDone: (y: SchoolYear) => void) {
  const t = (c: string) => year?.terms.find((x) => x.code === c);
  const [v, setV] = useState({
    code: year?.code ?? suggest ?? "",
    name: year?.name ?? "",
    start_date: year?.start_date ?? "",
    end_date: year?.end_date ?? "",
    hk1_start: t("hk1")?.start_date ?? "",
    hk1_end: t("hk1")?.end_date ?? "",
    hk2_start: t("hk2")?.start_date ?? "",
    hk2_end: t("hk2")?.end_date ?? "",
  });
  const save = useSaveSchoolYearMutation();
  const { fields, message } = formErrors(save.error);
  return {
    v,
    setV,
    set: (k: keyof typeof v) => (e: React.ChangeEvent<HTMLInputElement>) => setV({ ...v, [k]: e.target.value }),
    busy: save.isPending,
    fields,
    message,
    submit: () => {
      const terms =
        v.hk1_start && v.hk1_end && v.hk2_start && v.hk2_end
          ? [
              { code: "hk1" as const, start_date: v.hk1_start, end_date: v.hk1_end },
              { code: "hk2" as const, start_date: v.hk2_start, end_date: v.hk2_end },
            ]
          : undefined;
      const body = { name: v.name || null, start_date: v.start_date || null, end_date: v.end_date || null, terms };
      save.mutate(year ? { id: year.id, body } : { body: { ...body, code: v.code } }, { onSuccess: onDone });
    },
  };
}
