import { useMemo, useState } from "react";
import { toast } from "sonner";
import { useAddClassMembersMutation, useRemoveClassMembersMutation } from "@/hooks/react-query/use-query-class";
import { ApiError } from "@/lib/common/http";
import { qs, useApi } from "@/lib/hooks";
import type { Page, User } from "@/lib/types";

/** Students of one class: add from a search, remove selected rows. The members table reads the users list
 *  (GET /users?class_id=…), which moves with the identity slice; until then it reloads by key. */
export function useMemberManager(classId: string) {
  const [adding, setAdding] = useState(false);
  const [version, setVersion] = useState(0);
  const add = useAddClassMembersMutation(classId);
  const remove = useRemoveClassMembersMutation(classId);
  const params = useMemo(() => ({ class_id: classId }), [classId]);
  return {
    adding,
    setAdding,
    params,
    version,
    addStudent: async (userId: string): Promise<boolean> => {
      try {
        await add.mutateAsync([userId]);
        setVersion((v) => v + 1);
        return true;
      } catch (e) {
        toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
        return false;
      }
    },
    removeStudents: (rows: User[]) => remove.mutateAsync(rows.map((u) => u.id)),
  };
}

/** Students matching `q` (≥ 2 characters) for the add dialog. */
export function useStudentSearch(q: string) {
  return useApi<Page<User>>(q.trim().length >= 2 ? `/users${qs({ q, role: "student", page_size: 20 })}` : null).data;
}
