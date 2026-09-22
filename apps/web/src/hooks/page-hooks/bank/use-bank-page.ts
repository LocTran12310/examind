import { useEffect, useMemo, useState } from "react";
import { NO_SUBJECT } from "@/constants/question.constant";
import { useMeMaybe } from "@/hooks/common/use-me";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useQuestionFacetsQuery, useQuestionSearchQuery } from "@/hooks/react-query/use-query-question";
import { useTagOptionsQuery } from "@/hooks/react-query/use-query-tag";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { useTopicsQuery } from "@/hooks/react-query/use-query-topic";
import { bankSearchBody, SUBJECT_SCOPED } from "@/lib/page-libs/bank/filters";
import { useBankSubjectStore } from "@/stores/common/bank-subject.store";

/** The bank inside one subject: filters in the URL, facet counts, the page of questions and the selection. */
export function useBankPage() {
  const me = useMeMaybe();
  const orgId = me?.org.id ?? "";
  const tq = useTableQuery();
  const subject = tq.apiParams.get("subject_id") ?? "";
  const body = useMemo(() => bankSearchBody(tq.apiParams), [tq.apiParams]);
  const bodyKey = JSON.stringify(body);
  const { data: taxonomy } = useTaxonomyQuery();
  // counts per subject/topic/tag… for the tabs and the sheet; also picks the default subject
  const { data: facets } = useQuestionFacetsQuery(body);
  const list = useQuestionSearchQuery(body, { enabled: !!subject });
  const scoped = subject && subject !== NO_SUBJECT ? subject : null;
  const { data: topics } = useTopicsQuery(scoped, !!scoped);
  const { data: tags } = useTagOptionsQuery(scoped || "shared", !!(scoped || subject));
  const load = useBankSubjectStore((s) => s.load);
  const choose = useBankSubjectStore((s) => s.choose);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  useEffect(() => setSelected(new Set()), [bodyKey]);
  useEffect(() => {
    if (orgId) load(orgId);
  }, [orgId, load]);

  // no subject in the URL: the last one used here, else the one with most questions (A-01, A-03)
  useEffect(() => {
    if (subject || !taxonomy || !facets) return;
    const counts = facets.subjects;
    if (orgId) load(orgId);
    const last = orgId ? (useBankSubjectStore.getState().chosen[orgId] ?? null) : null;
    const best = [...taxonomy.subjects].sort((a, b) => (counts[b.id] ?? 0) - (counts[a.id] ?? 0))[0]?.id;
    const pick = last && (taxonomy.subjects.some((x) => x.id === last) || last === NO_SUBJECT) ? last : best;
    if (pick) tq.setFilters({ subject_id: pick });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subject, taxonomy, facets]);

  function chooseSubject(id: string) {
    if (orgId) choose(orgId, id);
    tq.setFilters({ subject_id: id, ...Object.fromEntries(SUBJECT_SCOPED.map((k) => [k, null])) });
  }

  const filters = useMemo(
    () => Object.fromEntries([...tq.apiParams.entries()].filter(([k]) => k !== "page" && k !== "page_size" && k !== "subject_id")),
    [tq.apiParams],
  );
  const data = list.data;
  const items = data?.data ?? [];
  const allOnPage = items.length > 0 && items.every((q) => selected.has(q.id));
  const toggle = (id: string) =>
    setSelected((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  return {
    tq,
    subject,
    scoped,
    taxonomy,
    facets,
    topics,
    tags,
    total: data?.total,
    items,
    loaded: !!data,
    loading: list.isFetching,
    reload: () => void list.refetch(),
    filters,
    subjectName: taxonomy?.subjects.find((x) => x.id === subject)?.name ?? (subject === NO_SUBJECT ? "Chưa phân môn" : undefined),
    chooseSubject,
    selected,
    toggle,
    allOnPage,
    selectPage: (on: boolean) => setSelected(on ? new Set([...selected, ...items.map((q) => q.id)]) : new Set()),
    clearSelection: () => setSelected(new Set()),
  };
}
