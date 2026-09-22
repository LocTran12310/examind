import { useRouter } from "next/navigation";
import { useState } from "react";
import { useCreateExamMutation } from "@/hooks/react-query/use-query-exam";
import { formErrors } from "@/lib/common/form-errors";

/** "Tạo đề mới": a title, then the exam page to build it. */
export function useNewExamForm() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const create = useCreateExamMutation();
  const { fields, message } = formErrors(create.error);
  return {
    title,
    setTitle,
    fields,
    message,
    busy: create.isPending,
    submit: () => create.mutate({ title }, { onSuccess: (exam) => router.push(`/org/exams/${exam.id}`) }),
  };
}
