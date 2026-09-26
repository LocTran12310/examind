import { useCallback, useEffect, useMemo, useState } from "react";

import { toast } from "sonner";
import { useAddClassMembersMutation, useClassOptionsQuery, useRemoveClassMembersMutation } from "@/hooks/react-query/use-query-class";
import { useUserOptionsQuery, useUserSearchQuery } from "@/hooks/react-query/use-query-user";
import type { User } from "@/interfaces/user.interface";
import { ApiError } from "@/lib/common/http";

/** one page of the wider search; matches beyond it are counted and said, not quietly dropped */
const LIMIT = 50;
/** the row input is a dropdown, not a list to read: it offers this many and says how many more matched */
const SUGGEST = 8;
/** a single letter matches the whole school, so nothing is searched until there are two */
const MIN_Q = 2;

/** add or drop one id of a selection */
const flip = (id: string) => (s: Set<string>) => {
  const next = new Set(s);
  if (!next.delete(id)) next.add(id);
  return next;
};

/** add or drop one student of a selection; the selection keeps the rows, not only their ids, because the draft
 *  list it feeds shows each name, username and class */
const flipUser = (u: User) => (m: Map<string, User>) => {
  const next = new Map(m);
  if (!next.delete(u.id)) next.set(u.id, u);
  return next;
};

/** Why this student cannot be taken now. The row stays listed and says this instead of vanishing (A-07): learning
 *  "em ấy đã ở trong lớp" beats concluding the student does not exist. */
const noteOf = (u: User, targetId: string, staged: ReadonlySet<string>) =>
  u.class_ids.includes(targetId) ? "đã ở trong lớp" : staged.has(u.id) ? "đã trong danh sách" : "";

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
    /** everything staged — one request, not one per student, however many classes it came from (AC-08) */
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

/** The add dialog: the draft list of who is about to be added, and the row input that grows it.
 *
 *  Nothing here is saved until the footer sends it, so a name typed by hand and twenty-five ticked in the picker
 *  are the same kind of row and leave in the same request. Two characters start the search; a student already in
 *  the target class, or already on the list, is offered but not takeable. */
export function useStudentStaging(targetId: string) {
  const [staged, setStaged] = useState<User[]>([]);
  const [q, setQ] = useState("");
  const { data: classes } = useClassOptionsQuery();
  const term = q.trim();
  const searching = term.length >= MIN_Q;
  const body = useMemo(() => ({ page: 1, limit: SUGGEST, q: term, filters: { role: { value: "student" } } }), [term]);
  const { data } = useUserSearchQuery(body, { enabled: searching });
  const ids = useMemo(() => new Set(staged.map((u) => u.id)), [staged]);
  const page = searching ? data : undefined;
  const matches = page?.data ?? [];
  const note = useCallback((u: User) => noteOf(u, targetId, ids), [targetId, ids]);
  return {
    staged,
    ids,
    q,
    setQ,
    searching,
    matches,
    note,
    /** matches this search found but the dropdown does not show — said out loud rather than silently cut off */
    more: Math.max(0, (page?.total ?? 0) - matches.length),
    /** the class each student is in today, which is what makes two names that look alike tellable apart */
    classLabel: (u: User) => {
      const names = (classes ?? []).filter((c) => u.class_ids.includes(c.id)).map((c) => `Lớp ${c.name}`);
      return names.length ? names.join(", ") : "Chưa có lớp";
    },
    /** whoever cannot be taken is dropped here as well, so no route into the list can stage a student twice */
    stage: (users: User[]) =>
      setStaged((rows) => {
        const have = new Set(rows.map((u) => u.id));
        return [...rows, ...users.filter((u) => !have.has(u.id) && !u.class_ids.includes(targetId))];
      }),
    unstage: (id: string) => setStaged((rows) => rows.filter((u) => u.id !== id)),
    clearQuery: () => setQ(""),
  };
}

export type StudentStaging = ReturnType<typeof useStudentStaging>;

/** The picker dialog: every other class of the organisation as one table, each row folded over its own roster,
 *  and the same students by name when the search box is used — one selection across all of it.
 *
 *  Every class is offered, not only last year's (A-06): a new class is sometimes filled from two old ones, or from
 *  a class of the same year when one is split — which is why the selection is kept here, above the rows, instead of
 *  inside the one class being looked at. Confirming hands the selection to the draft list; it saves nothing. */
export function useClassAdder(targetId: string, staged: ReadonlySet<string>) {
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [picked, setPicked] = useState<Map<string, User>>(new Map());
  // a class ticked while folded: its students are not known at click time, so the tick waits here for the roster
  const [wanted, setWanted] = useState<Set<string>>(new Set());
  const [q, setQ] = useState("");
  const { data: classes } = useClassOptionsQuery();
  const sources = useMemo(
    () => (classes ?? []).filter((c) => c.id !== targetId).sort((a, b) => b.school_year.localeCompare(a.school_year) || a.name.localeCompare(b.name)),
    [classes, targetId],
  );
  const term = q.trim();
  const searching = term.length >= MIN_Q;
  const body = useMemo(() => ({ page: 1, limit: LIMIT, q: term, filters: { role: { value: "student" } } }), [term]);
  const { data } = useUserSearchQuery(body, { enabled: searching });
  const note = useCallback((u: User) => noteOf(u, targetId, staged), [targetId, staged]);
  // Whoever cannot be taken cannot be ticked, and they sort first by name — so the first screenful of a search run
  // from inside a class was entirely rows you cannot tick. They stay listed (see `noteOf`) but they go last. The
  // order is of this page only, which is why the page says how many matches it is not showing.
  const page = searching ? data : undefined;
  const rows = useMemo(() => {
    const all = page?.data ?? [];
    return [...all.filter((u) => !note(u)), ...all.filter((u) => note(u))];
  }, [page, note]);
  const pick = useCallback((users: User[]) => setPicked((m) => new Map([...m, ...users.map((u) => [u.id, u] as const)])), []);
  const fill = useCallback(
    (sourceId: string, users: User[]) => {
      pick(users);
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
    q,
    setQ,
    searching,
    /** typed too little to search yet: the box says so instead of answering with an empty list */
    short: term.length > 0 && !searching,
    rows,
    note,
    /** matches this search found but this page does not show */
    more: Math.max(0, (page?.total ?? 0) - rows.length),
    isOpen: (id: string) => open.has(id),
    isWanted: (id: string) => wanted.has(id),
    toggleOpen: (id: string) => setOpen(flip(id)),
    toggle: (u: User) => setPicked(flipUser(u)),
    pick,
    unpick: (ids: string[]) => setPicked((m) => new Map([...m].filter(([id]) => !ids.includes(id)))),
    /** ticked before the roster is there: open the row too, because a tick that chooses 25 names should show them */
    want: (id: string) => {
      setWanted((s) => new Set(s).add(id));
      setOpen((s) => new Set(s).add(id));
    },
    fill,
    toggleAll: () => {
      const addable = rows.filter((u) => !note(u));
      setPicked((m) => (addable.every((u) => m.has(u.id)) ? new Map() : new Map(addable.map((u) => [u.id, u]))));
    },
  };
}

export type ClassAdder = ReturnType<typeof useClassAdder>;

/** One source class's roster, loaded while its row is open. `addable` leaves out whoever cannot be taken — already
 *  in the target class, or already on the draft list — and a tick left waiting by `want` is applied here: on the
 *  answer, not on the click. */
export function useClassRoster(a: ClassAdder, sourceId: string) {
  const { fill, note } = a;
  const enabled = a.isOpen(sourceId);
  const pending = a.isWanted(sourceId);
  const { data } = useUserOptionsQuery({ class_id: sourceId, filters: { role: { value: "student" } } }, enabled);
  const addable = useMemo(() => (data ?? []).filter((u) => !note(u)), [data, note]);
  useEffect(() => {
    if (pending && data) fill(sourceId, addable);
  }, [pending, data, addable, sourceId, fill]);
  return { students: data ?? [], addable, loaded: data !== undefined, loading: enabled && data === undefined };
}
