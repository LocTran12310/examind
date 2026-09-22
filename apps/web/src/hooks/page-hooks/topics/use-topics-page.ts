import { useEffect, useState } from "react";
import { useMe } from "@/hooks/common/use-me";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { useTopicsQuery } from "@/hooks/react-query/use-query-topic";

/** The subject shown (Toán first) and its tree; students only read it. */
export function useTopicsPage() {
  const me = useMe();
  const { data: taxonomy } = useTaxonomyQuery();
  const [subjectId, setSubjectId] = useState("");
  useEffect(() => {
    if (!subjectId && taxonomy?.subjects.length) setSubjectId((taxonomy.subjects.find((s) => s.code === "toan") ?? taxonomy.subjects[0]).id);
  }, [taxonomy, subjectId]);
  const { data: topics } = useTopicsQuery(subjectId || null, !!subjectId);
  return {
    subjectId,
    setSubjectId,
    subjectOptions: (taxonomy?.subjects ?? []).map((s) => ({ value: s.id, label: s.name })),
    topics,
    readOnly: me.role === "student",
  };
}
