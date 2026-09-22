import type { SearchBody } from "@/dtos/search.dto";

/** `POST /audit/search`: the history of one target, one org, or anything mentioning a user. */
export interface AuditSearchBody extends SearchBody {
  target_id?: string;
  organization_id?: string;
  related?: string;
}
