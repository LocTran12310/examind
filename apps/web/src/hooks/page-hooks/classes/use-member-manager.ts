import { useMemo, useState } from "react";
import { toast } from "sonner";
import { useAddClassMembersMutation, useRemoveClassMembersMutation } from "@/hooks/react-query/use-query-class";
import { useUserSearchQuery } from "@/hooks/react-query/use-query-user";
import type { User } from "@/interfaces/user.interface";
import { ApiError } from "@/lib/common/http";

/** Students of one class (`POST /users/search` with `class_id`): add from a search, remove selected rows;
 *  the member mutations refresh the users queries. */
export function useMemberManager(classId: string) {
  const [adding, setAdding] = useState(false);
  const add = useAddClassMembersMutation(classId);
  const remove = useRemoveClassMembersMutation(classId);
  const params = useMemo(() => ({ class_id: classId }), [classId]);
  return {
    adding,
    setAdding,
    params,
    addStudent: async (userId: string): Promise<boolean> => {
      try {
        await add.mutateAsync([userId]);
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
export function useStudentSearch(q: string): User[] | undefined {
  const term = q.trim();
  const body = { page: 1, limit: 20, q: term, filters: { role: { value: "student" } } };
  return useUserSearchQuery(body, { enabled: term.length >= 2 }).data?.data;
}
