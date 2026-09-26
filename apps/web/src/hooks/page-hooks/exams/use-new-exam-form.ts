import { useRouter } from "next/navigation";
import { useState } from "react";
import { useCreateExamMutation } from "@/hooks/react-query/use-query-exam";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import { formErrors } from "@/lib/common/form-errors";

/** "Tạo đề mới": a title, the subject and grade it is for, then the exam page to build it.
 *
 *  Both labels are optional (A-02) — a draft may not know its grade yet — but they are asked here because the
 *  subject is what scopes the matrix: an exam created without one opens the topic tree of every subject. */
export function useNewExamForm() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [grade, setGrade] = useState("");
  const { data: taxonomy } = useTaxonomyQuery();
  const create = useCreateExamMutation();
  const { fields, message } = formErrors(create.error);
  return {
    title,
    setTitle,
    subjectId,
    setSubjectId,
    grade,
    setGrade,
    subjects: taxonomy?.subjects ?? [],
    grades: taxonomy?.grades ?? [],
    fields,
    message,
    busy: create.isPending,
    submit: () =>
      create.mutate(
        { title, subject_id: subjectId || null, grade: grade ? Number(grade) : null },
        { onSuccess: (exam) => router.push(`/org/exams/${exam.id}`) },
      ),
  };
}
