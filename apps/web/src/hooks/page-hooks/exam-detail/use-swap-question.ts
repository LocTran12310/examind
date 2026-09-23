import { useMemo, useState } from "react";
import type { QuestionSearchBody } from "@/dtos/question.dto";
import { useQuestionSearchQuery, useTopicCountsQuery } from "@/hooks/react-query/use-query-question";
import { useTagOptionsQuery } from "@/hooks/react-query/use-query-tag";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { useTopicsQuery } from "@/hooks/react-query/use-query-topic";
import type { ExamQuestion } from "@/interfaces/exam.interface";

/** how many candidates the chooser shows at once; narrowing the filters is what finds the right one */
const LIMIT = 20;

/** The bank behind "Đổi câu": its search and its usual filters (subject, chuyên đề, loại, mức độ, tag),
 *  scoped by default to the subject of the exam and to the type of the question being replaced (ADR-03).
 *  A question already in the exam, or of another type, cannot be chosen — the position keeps its part and
 *  its points, and both come from the type. */
export function useSwapQuestion(question: ExamQuestion, examSubjectId: string | null) {
  const [q, setQ] = useState("");
  const [subjectId, setSubjectId] = useState(examSubjectId ?? question.subject_id ?? "");
  const [topicId, setTopicId] = useState<string | null>(null);
  const [type, setType] = useState<string>(question.type);
  const [difficulty, setDifficulty] = useState("");
  const [tagId, setTagId] = useState("");
  const [picking, setPicking] = useState(false);

  const { data: taxonomy } = useTaxonomyQuery();
  // "Mọi môn" keeps the whole tree and the whole bank's counts, so the numbers match what is listed
  const { data: topics } = useTopicsQuery(subjectId || null);
  const { data: tags } = useTagOptionsQuery(subjectId || null);
  const { data: counts } = useTopicCountsQuery(subjectId, true, true);

  const body = useMemo<QuestionSearchBody>(
    () => ({
      page: 1,
      limit: LIMIT,
      ...(q ? { q } : {}),
      ...(subjectId ? { subject_id: subjectId } : {}),
      ...(topicId ? { topic_id: topicId } : {}),
      ...(type ? { type } : {}),
      ...(difficulty ? { difficulty } : {}),
      ...(tagId ? { tag_ids: [tagId] } : {}),
    }),
    [q, subjectId, topicId, type, difficulty, tagId],
  );
  const list = useQuestionSearchQuery(body);
  const topic = topicId ? (topics ?? []).find((t) => t.id === topicId) : undefined;

  return {
    q,
    setQ,
    subjectId,
    setSubject: (v: string) => {
      setSubjectId(v);
      setTopicId(null); // a topic and a tag belong to one subject
      setTagId("");
    },
    topicId,
    topic,
    setTopicId,
    type,
    setType,
    difficulty,
    setDifficulty,
    tagId,
    setTagId,
    picking,
    setPicking,
    subjects: taxonomy?.subjects ?? [],
    topics: topics ?? [],
    tags: tags ?? [],
    counts,
    found: list.data?.data ?? [],
    total: list.data?.total ?? 0,
    loading: list.isFetching,
    loaded: !!list.data,
  };
}
