import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import type { Option } from "@/components/common/OptionSelect/OptionSelect";
import type { QuestionSearchBody } from "@/dtos/question.dto";
import { useHotkeys } from "@/hooks/common/use-hotkeys";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useDocumentSearchQuery } from "@/hooks/react-query/use-query-document";
import { useBulkTopicsMutation, useBulkUpdateQuestionsMutation, useQuestionFacetsQuery, useQuestionSearchQuery, useTopicCountsQuery, useTopicSuggestionsQuery } from "@/hooks/react-query/use-query-question";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { useTopicsQuery } from "@/hooks/react-query/use-query-topic";
import type { SourceDocument } from "@/interfaces/document.interface";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { Topic } from "@/interfaces/topic.interface";
import { ApiError } from "@/lib/common/http";
import { assignSummary, suggestionPairs } from "@/lib/page-libs/tagging-queue/assign";
import { queueRows, type QueueSuggestion } from "@/lib/page-libs/tagging-queue/rows";

const NEWEST = [{ field: "created_at", desc: true }];
// the whole backlog is worked from one screen: every status, not just the usable ones (A-04, ADR-02)
const EVERY_STATUS = "all";
/** the document filter loads a page at a time and asks for the next as it is scrolled (A-07) */
const DOCUMENT_PAGE = 50;
const NO_ROWS: ParsedQuestion[] = [];
const NO_DOCS: SourceDocument[] = [];
/** the bulk picker's own value of `picking` (a row's is its question id) */
export const BULK = "bulk";

/**
 * "Chưa gắn chuyên đề" (topic-coverage UOW-02): the page of untagged questions, the suggestions of the
 * ids on it, the selection and the keyboard flow. Assignment is the bank's bulk command, for one row
 * and for the selection alike, so the list, the counter and the facets refresh from the server.
 */
export function useTaggingQueue() {
  const tq = useTableQuery();
  const subjectId = tq.get("subject_id");
  const documentId = tq.get("document_id");
  const body = useMemo<QuestionSearchBody>(
    () => ({
      has_topic: false,
      page: tq.page,
      limit: tq.pageSize,
      sort: NEWEST,
      status: EVERY_STATUS,
      ...(subjectId ? { subject_id: subjectId } : {}),
      ...(documentId ? { document_id: documentId } : {}),
    }),
    [tq.page, tq.pageSize, subjectId, documentId],
  );
  // the document counts must not shrink to the chosen document (AC-05)
  const facetsBody = useMemo<QuestionSearchBody>(() => ({ ...body, document_id: undefined }), [body]);
  const list = useQuestionSearchQuery(body);
  const { data: facets } = useQuestionFacetsQuery(facetsBody);
  const { data: taxonomy } = useTaxonomyQuery();
  const { data: topics } = useTopicsQuery(null);
  // the papers arrive a page at a time; what has been loaded is kept, so the filter grows as it is scrolled
  const [documentPage, setDocumentPage] = useState(1);
  const documentsBody = useMemo(() => ({ page: documentPage, limit: DOCUMENT_PAGE, sort: NEWEST }), [documentPage]);
  const documents = useDocumentSearchQuery(documentsBody);
  const [loadedDocuments, setLoadedDocuments] = useState<SourceDocument[]>(NO_DOCS);
  useEffect(() => {
    const page = documents.data?.data;
    if (!page?.length) return;
    setLoadedDocuments((prev) => {
      const byId = new Map(prev.map((d) => [d.id, d]));
      for (const d of page) byId.set(d.id, d);
      return byId.size === prev.length ? prev : [...byId.values()];
    });
  }, [documents.data]);
  const moreDocuments = loadedDocuments.length < (documents.data?.total ?? 0);
  const items = list.data?.data ?? NO_ROWS;
  const ids = useMemo(() => items.map((q) => q.id), [items]);
  // the rules answer at once; the model takes tens of seconds, so it arrives on its own and replaces them
  const { data: ruleSuggestions } = useTopicSuggestionsQuery(ids);
  const { data: modelSuggestions, isFetching: modelPending } = useTopicSuggestionsQuery(ids, true);
  const suggestions = modelSuggestions ?? ruleSuggestions;
  const { mutateAsync: bulk } = useBulkUpdateQuestionsMutation();
  const { mutateAsync: bulkTopics } = useBulkTopicsMutation();

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [focus, setFocus] = useState(0);
  const [picking, setPicking] = useState<string | null>(null);
  const bodyKey = JSON.stringify(body);
  useEffect(() => {
    setSelected(new Set());
    setFocus(0);
  }, [bodyKey]);

  const topicsById = useMemo(() => new Map((topics ?? []).map((t) => [t.id, t])), [topics]);
  const docsById = useMemo(() => new Map(loadedDocuments.map((d) => [d.id, d])), [loadedDocuments]);
  const rows = useMemo(
    () => queueRows(items, { suggestions: suggestions ?? {}, topicsById, documents: docsById, taxonomy }),
    [items, suggestions, topicsById, docsById, taxonomy],
  );
  const at = Math.min(focus, Math.max(0, rows.length - 1));

  async function assign(target: string[], topicId: string, what: string) {
    if (!target.length) return;
    try {
      const r = await bulk({ ids: target, set: { primary_topic_id: topicId } });
      toast.success(target.length > 1 ? `Đã gán chuyên đề cho ${r.updated} câu` : `Đã gán chuyên đề ${what}`);
      setSelected(new Set());
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  const applySuggestion = (questionId: string, s: QueueSuggestion) => void assign([questionId], s.topic_id, s.label);

  /** Each selected row takes its own top suggestion, in one request (AC-03, ADR-02). What had no
   *  suggestion is left alone, and it and whatever the server skipped are named in the answer. */
  async function applySuggestions() {
    const { pairs, noSuggestion } = suggestionPairs(rows.filter((r) => selected.has(r.q.id)));
    if (!pairs.length) {
      toast.error(`${noSuggestion} câu chưa có gợi ý`);
      return;
    }
    try {
      const r = await bulkTopics({ pairs });
      toast.success(assignSummary(r.updated, noSuggestion, r.skipped ?? []));
      setSelected(new Set());
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  function applyNth(n: number) {
    const row = rows[at];
    const s = row?.suggestions[n];
    if (s) applySuggestion(row.q.id, s);
  }

  function pickTopic(t: Topic) {
    const target = picking === BULK ? [...selected] : picking ? [picking] : [];
    setPicking(null);
    void assign(target, t.id, t.name);
  }

  useHotkeys(
    {
      ArrowDown: () => setFocus(Math.min(at + 1, rows.length - 1)),
      ArrowUp: () => setFocus(Math.max(at - 1, 0)),
      "1": () => applyNth(0),
      "2": () => applyNth(1),
      "3": () => applyNth(2),
    },
    !picking,
  );

  // a topic belongs to one subject: a row is picked inside its own subject, the selection inside its common one
  const selectedRows = rows.filter((r) => selected.has(r.q.id));
  const selectedSubjects = new Set(selectedRows.map((r) => r.q.subject_id ?? ""));
  const pickingRow = rows.find((r) => r.q.id === picking);
  const pickingSubject = picking === BULK ? [...selectedSubjects][0] : pickingRow?.q.subject_id;
  const pickerTopics = useMemo(() => (pickingSubject ? (topics ?? []).filter((t) => t.subject_id === pickingSubject) : (topics ?? [])), [topics, pickingSubject]);
  // the numbers beside the topics are questions of that subject, from the facets (ADR-01)
  const { data: topicCounts } = useTopicCountsQuery(pickingSubject);

  // no count beside a subject: the subjects facet drops the topic dimension, so it counts every question, not the untagged ones
  const subjectOptions: Option[] = (taxonomy?.subjects ?? []).map((s) => ({ value: s.id, label: s.name }));
  const counts = facets?.untagged_documents;
  const documentOptions: Option[] = loadedDocuments
    .filter((d) => !counts || counts[d.id])
    .map((d) => ({ value: d.id, label: counts?.[d.id] ? `${d.filename} (${counts[d.id]})` : d.filename }));

  const toggle = (id: string) =>
    setSelected((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  return {
    tq,
    rows,
    at,
    setFocus,
    total: list.data?.total,
    loaded: !!list.data,
    loading: list.isFetching,
    /** the model is still working on this page's suggestions */
    modelPending: modelPending && !modelSuggestions,
    reload: () => void list.refetch(),
    subjectId,
    documentId,
    subjectOptions,
    documentOptions,
    /** scrolling to the end of the filter asks for the next page of papers, while there is one (A-07) */
    loadMoreDocuments: () => {
      if (moreDocuments && !documents.isFetching) setDocumentPage((p) => p + 1);
    },
    loadingDocuments: documents.isFetching && moreDocuments,
    setFilter: (name: string, value: string) => tq.setFilter(name, value || null),
    selected,
    toggle,
    allOnPage: rows.length > 0 && rows.every((r) => selected.has(r.q.id)),
    selectPage: (on: boolean) => setSelected(on ? new Set(rows.map((r) => r.q.id)) : new Set()),
    clearSelection: () => setSelected(new Set()),
    /** the selection spans several subjects: one topic cannot cover it */
    mixedSubjects: selectedSubjects.size > 1,
    picking,
    setPicking,
    pickerTopics,
    pickerCounts: topicCounts,
    /** the picker of one row opens on that row's own top suggestion, applying nothing (A-01) */
    pickerInitial: picking === BULK ? null : (pickingRow?.suggestions[0]?.topic_id ?? null),
    pickerTitle: picking === BULK ? `Gán chuyên đề cho ${selected.size} câu` : "Chọn chuyên đề cho câu này",
    pickTopic,
    applySuggestion,
    applySuggestions: () => void applySuggestions(),
    /** how many of the selected questions have a suggestion to take */
    suggestable: selectedRows.filter((r) => r.suggestions.length > 0).length,
  };
}
