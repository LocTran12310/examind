import { create } from "zustand";

/** The subject last used in the bank, per organisation, remembered in this browser (subject-scoped-bank A-01).
 *  Each org keeps its own key (`examind.bank.subject.<org>`). */
const key = (orgId: string) => `examind.bank.subject.${orgId}`;

function stored(orgId: string): string | null {
  try {
    return localStorage.getItem(key(orgId));
  } catch {
    return null;
  }
}

interface BankSubjectStore {
  /** org id → last subject id (or "none"), loaded from the browser on first read */
  chosen: Record<string, string | null>;
  load: (orgId: string) => void;
  choose: (orgId: string, subjectId: string) => void;
}

export const useBankSubjectStore = create<BankSubjectStore>((set, get) => ({
  chosen: {},
  load: (orgId) => {
    if (!(orgId in get().chosen)) set((s) => ({ chosen: { ...s.chosen, [orgId]: stored(orgId) } }));
  },
  choose: (orgId, subjectId) => {
    try {
      localStorage.setItem(key(orgId), subjectId);
    } catch {}
    set((s) => ({ chosen: { ...s.chosen, [orgId]: subjectId } }));
  },
}));
