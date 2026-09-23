import type { SearchBody } from "@/dtos/search.dto";
import type { DocumentQuestionState, ReviewAction } from "@/interfaces/review.interface";

/** Body of `POST /review/documents/search`; `mine` = only documents assigned to me. */
export interface ReviewDocumentSearchBody extends SearchBody {
  mine?: boolean;
}

/** Body of `POST /review/documents/{id}/questions/search`; `state` narrows to what was decided (review-ux AC-03). */
export interface DocumentQuestionSearchBody extends SearchBody {
  state?: DocumentQuestionState;
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
