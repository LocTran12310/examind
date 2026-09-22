import type { UseQueryResult } from "@tanstack/react-query";
import { AUDIT_KEYS } from "@/constants/react-query-key.constant";
import type { AuditSearchBody } from "@/dtos/audit.dto";
import type { AuditEntry } from "@/interfaces/audit.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { auditService } from "@/services/audit.service";
import { useSearchQuery } from "./use-search-query";

export function useAuditSearchQuery(body: AuditSearchBody, options?: RowsQueryOptions<AuditEntry>): UseQueryResult<SearchPage<AuditEntry>, Error> {
  return useSearchQuery(AUDIT_KEYS.SEARCH(body), auditService.search, body, options);
}
