import type { AuditEntry } from "@/interfaces/audit.interface";

/** One line of what changed: `field: before → after`, the names involved, how many people. */
export function auditDetails(e: AuditEntry): string {
  const d = e.data ?? {};
  const parts: string[] = [];
  const changes = d.changes as Record<string, [unknown, unknown]> | undefined;
  if (changes) for (const [k, [a, b]] of Object.entries(changes)) parts.push(`${k}: ${a ?? "—"} → ${b ?? "—"}`);
  for (const k of ["username", "name", "code", "school_year", "role", "home", "org_code"]) if (typeof d[k] === "string" && !changes?.[k]) parts.push(String(d[k]));
  if (Array.isArray(d.user_ids)) parts.push(`${d.user_ids.length} người`);
  return parts.join(" · ");
}
