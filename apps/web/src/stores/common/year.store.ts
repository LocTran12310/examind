import { create } from "zustand";

/** The school year chosen in the header, per organisation, remembered in this browser (school-years A-08).
 *  Each org keeps its own key (`examind.year.<org>`), so switching org never carries a year over. */
const key = (orgId: string) => `examind.year.${orgId}`;

function stored(orgId: string): string | null {
  try {
    return localStorage.getItem(key(orgId));
  } catch {
    return null;
  }
}

interface YearStore {
  /** org id → chosen year id (loaded from the browser on first read) */
  chosen: Record<string, string | null>;
  load: (orgId: string) => void;
  choose: (orgId: string, yearId: string) => void;
}

export const useYearStore = create<YearStore>((set, get) => ({
  chosen: {},
  load: (orgId) => {
    if (!(orgId in get().chosen)) set((s) => ({ chosen: { ...s.chosen, [orgId]: stored(orgId) } }));
  },
  choose: (orgId, yearId) => {
    try {
      localStorage.setItem(key(orgId), yearId);
    } catch {}
    set((s) => ({ chosen: { ...s.chosen, [orgId]: yearId } }));
  },
}));
