/**
 * Dates and times, one convention for the whole app (ui-standards ADR-02): the API stores and sends UTC (`…Z`); everything shown
 * or typed is on the business calendar, Asia/Ho_Chi_Minh (+07:00, no daylight saving), whatever the
 * browser's own zone. Date filters send plain `YYYY-MM-DD`; the server expands them to UTC bounds.
 */
export const BUSINESS_TZ = "Asia/Ho_Chi_Minh";
const OFFSET = "+07:00";

type Input = string | number | Date | null | undefined;

function toDate(v: Input): Date | null {
  if (v === null || v === undefined || v === "") return null;
  const d = v instanceof Date ? v : new Date(v);
  return Number.isNaN(d.getTime()) ? null : d;
}

const partsFmt = new Intl.DateTimeFormat("en-GB", {
  timeZone: BUSINESS_TZ,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hourCycle: "h23",
});

/** Calendar fields of an instant in the business zone. */
export function businessParts(v: Input): { y: string; m: string; d: string; hh: string; mm: string; ss: string } | null {
  const d = toDate(v);
  if (!d) return null;
  const p = Object.fromEntries(partsFmt.formatToParts(d).map((x) => [x.type, x.value]));
  return { y: p.year, m: p.month, d: p.day, hh: p.hour === "24" ? "00" : p.hour, mm: p.minute, ss: p.second };
}

/** `22/09/2026 17:45` (optionally with seconds); "—" for nothing. */
export function formatDateTime(v: Input, opts: { withSeconds?: boolean } = {}): string {
  const p = businessParts(v);
  if (!p) return "—";
  return `${p.d}/${p.m}/${p.y} ${p.hh}:${p.mm}${opts.withSeconds ? `:${p.ss}` : ""}`;
}

/** `22/09/2026`. A bare `YYYY-MM-DD` is a calendar day and is shown as is. */
export function formatDate(v: Input): string {
  if (typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v)) {
    const [y, m, d] = v.split("-");
    return `${d}/${m}/${y}`;
  }
  const p = businessParts(v);
  return p ? `${p.d}/${p.m}/${p.y}` : "—";
}

export function formatTime(v: Input): string {
  const p = businessParts(v);
  return p ? `${p.hh}:${p.mm}` : "—";
}

/** Today in the business zone, `YYYY-MM-DD` (default values of date filters and forms). */
export function businessToday(now: Input = new Date()): string {
  const p = businessParts(now)!;
  return `${p.y}-${p.m}-${p.d}`;
}

/** Value for `<Input type="datetime-local">`: the instant written in business time. */
export function toBusinessInput(v: Input): string {
  const p = businessParts(v);
  return p ? `${p.y}-${p.m}-${p.d}T${p.hh}:${p.mm}` : "";
}

/** `datetime-local` value (business time) → ISO with the explicit +07:00 offset (never offset-less). */
export function fromBusinessInput(v: string): string {
  if (!v) return "";
  const withSeconds = v.length === 16 ? `${v}:00` : v;
  return new Date(`${withSeconds}${OFFSET}`).toISOString();
}
