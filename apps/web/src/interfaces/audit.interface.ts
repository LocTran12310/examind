/** One history entry (`POST /audit/search`). */
export interface AuditEntry {
  id: string;
  created_at: string;
  organization_id: string;
  organization_code: string | null;
  actor_id: string | null;
  actor_name: string | null;
  action: string;
  target_type: string;
  target_id: string | null;
  data: Record<string, unknown>;
}
