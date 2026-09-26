import { useEffect, useMemo, useState } from "react";

import { toast } from "sonner";
import { useAddClassMembersMutation, useClassOptionsQuery, useRemoveClassMembersMutation } from "@/hooks/react-query/use-query-class";
import { useUserOptionsQuery, useUserSearchQuery } from "@/hooks/react-query/use-query-user";
import type { User } from "@/interfaces/user.interface";
import { ApiError } from "@/lib/common/http";

/** one page of the wider search; matches beyond it are counted and said, not quietly dropped */
const LIMIT = 50;

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
    /** a whole source class at once — one request, not one per student (AC-08) */
    addStudents: async (userIds: string[]): Promise<boolean> => {
      try {
        await add.mutateAsync(userIds);
        toast.success(`Đã thêm ${userIds.length} học sinh vào lớp`);
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

/** The wider search behind the magnifier: the same students, but narrowed by class as well as by name, several
 *  ticked at once, and honest about how many matched beyond the page it shows. */
export function useStudentFinder(classId: string) {
  const [q, setQ] = useState("");
  const [classFilter, setClassFilter] = useState("");
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const { data: classes } = useClassOptionsQuery();
  const body = useMemo(
    () => ({ page: 1, limit: LIMIT, q: q.trim(), filters: { role: { value: "student" } }, ...(classFilter ? { class_id: classFilter } : {}) }),
    [q, classFilter],
  );
  const { data } = useUserSearchQuery(body);
  const rows = data?.data ?? [];
  const already = useMemo(() => new Set(rows.filter((u) => u.class_ids.includes(classId)).map((u) => u.id)), [rows, classId]);
  return {
    q,
    setQ,
    classFilter,
    setClassFilter,
    classes: classes ?? [],
    rows,
    already,
    /** matches this search found but this page does not show — said out loud rather than silently cut off */
    more: Math.max(0, (data?.total ?? 0) - rows.length),
    picked,
    clear: () => setPicked(new Set()),
    toggle: (id: string) =>
      setPicked((s) => {
        const next = new Set(s);
        if (!next.delete(id)) next.add(id);
        return next;
      }),
    toggleAll: () => {
      const addable = rows.filter((u) => !already.has(u.id)).map((u) => u.id);
      setPicked((s) => (addable.every((id) => s.has(id)) ? new Set() : new Set(addable)));
    },
  };
}

/** "Từ lớp cũ": pick a source class, then its students — everyone ticked to begin with (A-05), and whoever is
 *  already in the target class locked out of the selection (A-07).
 *
 *  Every class of the organisation is offered, not only last year's (A-06): a new class is sometimes filled from
 *  two old ones, or from a class of the same year when one is split. */
export function useFromClass(classId: string) {
  const [sourceId, setSourceId] = useState<string | null>(null);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const { data: classes } = useClassOptionsQuery();
  const { data: students } = useUserOptionsQuery({ class_id: sourceId ?? undefined, filters: { role: { value: "student" } } }, !!sourceId);
  const already = useMemo(() => new Set((students ?? []).filter((u) => u.class_ids.includes(classId)).map((u) => u.id)), [students, classId]);

  // a fresh source class starts with everyone it can offer ticked; the effect runs on the answer, not on the
  // click, because the roster is not known yet when the class is chosen
  useEffect(() => {
    setPicked(new Set((students ?? []).filter((u) => !u.class_ids.includes(classId)).map((u) => u.id)));
  }, [students, classId]);

  const sources = useMemo(
    () => (classes ?? []).filter((c) => c.id !== classId).sort((a, b) => b.school_year.localeCompare(a.school_year) || a.name.localeCompare(b.name)),
    [classes, classId],
  );
  return {
    sources,
    sourceId,
    source: sources.find((c) => c.id === sourceId) ?? null,
    choose: (id: string | null) => {
      setSourceId(id);
      setPicked(new Set());
    },
    students: students ?? [],
    loading: !!sourceId && students === undefined,
    already,
    picked,
    toggle: (id: string) =>
      setPicked((s) => {
        const next = new Set(s);
        if (!next.delete(id)) next.add(id);
        return next;
      }),
  };
}
