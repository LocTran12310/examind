import type { UseQueryResult } from "@tanstack/react-query";
import { ACCOUNT_KEYS } from "@/constants/react-query-key.constant";
import type { SearchBody } from "@/dtos/search.dto";
import type { Account } from "@/interfaces/org.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { accountService } from "@/services/account.service";
import { useSearchQuery } from "./use-search-query";

export function useAccountSearchQuery(body: SearchBody, options?: RowsQueryOptions<Account>): UseQueryResult<SearchPage<Account>, Error> {
  return useSearchQuery(ACCOUNT_KEYS.SEARCH(body), accountService.search, body, options);
}
