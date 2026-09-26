import { useCallback, useEffect, useMemo, useState } from "react";

import { toast } from "sonner";
import { useAddClassMembersMutation, useClassOptionsQuery, useRemoveClassMembersMutation } from "@/hooks/react-query/use-query-class";
import { useUserOptionsQuery, useUserSearchQuery } from "@/hooks/react-query/use-query-user";
import type { User } from "@/interfaces/user.interface";
import { ApiError } from "@/lib/common/http";

/** one page of the wider search; matches beyond it are counted and said, not quietly dropped */
const LIMIT = 50;

/** add or drop one id of a selection */
const flip = (id: string) => (s: Set<string>) => {
  const next = new Set(s);
  if (!next.delete(id)) next.add(id);
  return next;
};

/** Students of one class (`POST /users/search` with `class_id`): add from the add dialog, remove selected rows;
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
    /** everything ticked — one request, not one per student, however many classes it came from (AC-08) */
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

/** The add dialog: every other class of the organisation as one table, each row folded over its own roster, and
 *  one selection across all of them.
 *
 *  Every class is offered, not only last year's (A-06): a new class is sometimes filled from two old ones, or from
 *  a class of the same year when one is split — which is why the selection is kept here, above the rows, instead of
 *  inside the one class being looked at. */
export function useClassAdder(targetId: string) {
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [picked, setPicked] = useState<Set<string>>(new Set());
  // a class ticked while folded: its students are not known at click time, so the tick waits here for the roster
  const [wanted, setWanted] = useState<Set<string>>(new Set());
  const { data: classes } = useClassOptionsQuery();
  const sources = useMemo(
    () => (classes ?? []).filter((c) => c.id !== targetId).sort((a, b) => b.school_year.localeCompare(a.school_year) || a.name.localeCompare(b.name)),
    [classes, targetId],
  );
  const pick = useCallback((ids: string[]) => setPicked((s) => new Set([...s, ...ids])), []);
  const fill = useCallback(
    (sourceId: string, ids: string[]) => {
      pick(ids);
      setWanted((s) => {
        const next = new Set(s);
        next.delete(sourceId);
        return next;
      });
    },
    [pick],
  );
  return {
    sources,
    picked,
    isOpen: (id: string) => open.has(id),
    isWanted: (id: string) => wanted.has(id),
    toggleOpen: (id: string) => setOpen(flip(id)),
    toggle: (id: string) => setPicked(flip(id)),
    pick,
    unpick: (ids: string[]) => setPicked((s) => new Set([...s].filter((id) => !ids.includes(id)))),
    /** ticked before the roster is there: open the row too, because a tick that chooses 25 names should show them */
    want: (id: string) => {
      setWanted((s) => new Set(s).add(id));
      setOpen((s) => new Set(s).add(id));
    },
    fill,
  };
}

export type ClassAdder = ReturnType<typeof useClassAdder>;

/** One source class's roster, loaded while its row is open. `addable` leaves out whoever is already in the target
 *  class, and a tick left waiting by `want` is applied here — on the answer, not on the click. */
export function useClassRoster(a: ClassAdder, sourceId: string, targetId: string) {
  const { fill } = a;
  const enabled = a.isOpen(sourceId);
  const pending = a.isWanted(sourceId);
  const { data } = useUserOptionsQuery({ class_id: sourceId, filters: { role: { value: "student" } } }, enabled);
  const addable = useMemo(() => (data ?? []).filter((u) => !u.class_ids.includes(targetId)).map((u) => u.id), [data, targetId]);
  useEffect(() => {
    if (pending && data) fill(sourceId, addable);
  }, [pending, data, addable, sourceId, fill]);
  return { students: data ?? [], addable, loaded: data !== undefined, loading: enabled && data === undefined };
}

/** "Tìm nâng cao": the same students, but narrowed by class as well as by name, several ticked at once, and honest
 *  about how many matched beyond the page it shows. */
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
  // Whoever is already in this class cannot be added, and they sort first by name — so the first screenful of a
  // search run from inside a class was entirely rows you cannot tick. They stay listed (learning "em ấy đã ở
  // trong lớp" beats concluding the student does not exist) but they go last. The order is of this page only,
  // which is why the page says how many matches it is not showing.
  const rows = useMemo(() => {
    const all = data?.data ?? [];
    const here = (u: User) => u.class_ids.includes(classId);
    return [...all.filter((u) => !here(u)), ...all.filter(here)];
  }, [data, classId]);
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
    toggle: (id: string) => setPicked(flip(id)),
    toggleAll: () => {
      const addable = rows.filter((u) => !already.has(u.id)).map((u) => u.id);
      setPicked((s) => (addable.every((id) => s.has(id)) ? new Set() : new Set(addable)));
    },
  };
}
