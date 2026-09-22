import type { AuditSearchBody } from "@/dtos/audit.dto";
import type { AuditEntry } from "@/interfaces/audit.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

export const auditService = {
  search: (body: AuditSearchBody) => http<SearchPage<AuditEntry>>("/audit/search", { body }),
};
