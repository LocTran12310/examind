import type { UseQueryResult } from "@tanstack/react-query";
import { ATTEMPT_KEYS } from "@/constants/react-query-key.constant";
import type { SearchBody } from "@/dtos/search.dto";
import type { AttemptHistoryRow } from "@/interfaces/attempt.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { attemptService } from "@/services/attempt.service";
import { useSearchQuery } from "./use-search-query";

/** Lượt làm bài của một người, mới nhất trước. Phạm vi thật do phiên quyết, không do `student_id` ở đây: một
 *  học sinh hỏi về bạn khác vẫn chỉ nhận được của chính mình. */
export function useAttemptSearchQuery(body: SearchBody, enabled = true): UseQueryResult<SearchPage<AttemptHistoryRow>, Error> {
  return useSearchQuery(ATTEMPT_KEYS.SEARCH(body), attemptService.search, body, { enabled });
}
