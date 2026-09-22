import type { SearchBody } from "@/dtos/search.dto";
import type { Account } from "@/interfaces/org.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

/** Every account of every org (super admin). */
export const accountService = {
  search: (body: SearchBody) => http<SearchPage<Account>>("/admin/users/search", { body }),
};
