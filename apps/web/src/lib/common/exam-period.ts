/**
 * "Đợt kiểm tra" = học kỳ × loại đề (school-years A-10): Giữa kỳ 1, Cuối kỳ 1, Giữa kỳ 2, Cuối kỳ 2, …
 * Stored in the existing semester_code + exam_kind fields; the value here is "hk1|Giữa kỳ".
 */
import { EXAM_KINDS } from "@/constants/document.constant";

const TERM_NO: Record<string, string> = { hk1: "1", hk2: "2" };
const PERIODIC = ["Giữa kỳ", "Cuối kỳ"];

export interface PeriodOption {
  value: string;
  label: string;
  group: string;
}

export function periodLabel(semester?: string | null, kind?: string | null): string {
  if (!semester && !kind) return "";
  if (kind && PERIODIC.includes(kind) && semester && TERM_NO[semester]) return `${kind} ${TERM_NO[semester]}`;
  if (!kind) return semester ? `Học kỳ ${TERM_NO[semester] ?? semester}` : "";
  return semester && TERM_NO[semester] ? `${kind} · HK${TERM_NO[semester]}` : kind;
}

export const periodValue = (semester?: string | null, kind?: string | null) => (semester || kind ? `${semester ?? ""}|${kind ?? ""}` : "");

export function parsePeriod(v: string): { semester_code: string | undefined; exam_kind: string | undefined } {
  const [s, k] = v.split("|");
  return { semester_code: s || undefined, exam_kind: k || undefined };
}

/** Options for pickers; `withTermOnly` adds "Học kỳ 1 (mọi loại)" for filters. */
export function periodOptions(withTermOnly = false): PeriodOption[] {
  const out: PeriodOption[] = [];
  for (const t of ["hk1", "hk2"])
    for (const k of PERIODIC) out.push({ value: periodValue(t, k), label: periodLabel(t, k), group: "Kiểm tra định kỳ" });
  for (const k of EXAM_KINDS.filter((k) => !PERIODIC.includes(k))) {
    for (const t of ["hk1", "hk2"]) out.push({ value: periodValue(t, k), label: periodLabel(t, k), group: "Khác" });
    out.push({ value: periodValue(null, k), label: k, group: "Khác" });
  }
  if (withTermOnly) for (const t of ["hk1", "hk2"]) out.push({ value: periodValue(t, null), label: `Học kỳ ${TERM_NO[t]} (mọi loại)`, group: "Theo học kỳ" });
  return out;
}
