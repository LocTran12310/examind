import type { SearchBody } from "@/dtos/search.dto";
import type { ReviewAction } from "@/interfaces/review.interface";

/** Body of `POST /review/documents/search`; `mine` = only documents assigned to me. */
export interface ReviewDocumentSearchBody extends SearchBody {
  mine?: boolean;
}

export interface UpdateReviewDocumentBody {
  assigned_to: string | null;
}

export interface ReviewActionBody {
  action: ReviewAction;
}

export interface AnswerKeyBody {
  text: string;
}
