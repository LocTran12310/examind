import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { DOCUMENT_KEYS, QUESTION_KEYS, REVIEW_KEYS } from "@/constants/react-query-key.constant";
import type { CheckDocumentsBody, CreateExamFromDocumentBody, ReparseDocumentBody, UpdateDocumentBody, UploadDocumentBody } from "@/dtos/document.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { DocumentExamResult, DuplicateCheck, SourceDocument, UploadResult } from "@/interfaces/document.interface";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";
import { invalidate } from "@/lib/common/query-client";
import { documentService } from "@/services/document.service";
import { useSearchQuery } from "./use-search-query";

// a document's questions live in the bank and in review too
const TOUCHED = [DOCUMENT_KEYS.ALL, QUESTION_KEYS.ALL, REVIEW_KEYS.ALL] as const;

/** Link to download a document's original file (a plain `<a href>`, not a query). */
export const documentFileUrl = documentService.fileUrl;

export function useDocumentSearchQuery(body: SearchBody, options?: RowsQueryOptions<SourceDocument>): UseQueryResult<SearchPage<SourceDocument>, Error> {
  return useSearchQuery(DOCUMENT_KEYS.SEARCH(body), documentService.search, body, options);
}

/** One document; `refetchInterval` of the last answer, e.g. poll while it is being processed. */
export function useDocumentQuery(id: string, refetchInterval?: (doc: SourceDocument | undefined) => number | false): UseQueryResult<SourceDocument, Error> {
  return useQuery<SourceDocument, Error>({
    queryKey: DOCUMENT_KEYS.DETAIL(id),
    queryFn: () => documentService.get(id),
    refetchInterval: refetchInterval ? (q) => refetchInterval(q.state.data) : false,
  });
}

/** The questions parsed from a document; `enabled` false until it is parsed. */
export function useDocumentQuestionsQuery(id: string, enabled: boolean): UseQueryResult<ParsedQuestion[], Error> {
  return useQuery<ParsedQuestion[], Error>({ queryKey: DOCUMENT_KEYS.QUESTIONS(id), queryFn: () => documentService.questions(id), enabled });
}

/** Duplicate check before an upload; nothing cached depends on it. */
export function useCheckDocumentsMutation(): UseMutationResult<DuplicateCheck[], Error, CheckDocumentsBody> {
  return useMutation<DuplicateCheck[], Error, CheckDocumentsBody>({ mutationFn: documentService.check });
}

export function useUploadDocumentMutation(): UseMutationResult<UploadResult, Error, UploadDocumentBody> {
  const qc = useQueryClient();
  return useMutation<UploadResult, Error, UploadDocumentBody>({
    mutationFn: documentService.upload,
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

export function useUpdateDocumentMutation(): UseMutationResult<SourceDocument, Error, { id: string; body: UpdateDocumentBody }> {
  const qc = useQueryClient();
  return useMutation<SourceDocument, Error, { id: string; body: UpdateDocumentBody }>({
    mutationFn: ({ id, body }) => documentService.update(id, body),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}

export function useDeleteDocumentsMutation(): UseMutationResult<void, Error, string[]> {
  const qc = useQueryClient();
  return useMutation<void, Error, string[]>({
    mutationFn: async (ids) => {
      for (const id of ids) await documentService.remove(id);
    },
    onSettled: () => invalidate(qc, ...TOUCHED),
  });
}

export function useCreateExamFromDocumentMutation(): UseMutationResult<DocumentExamResult, Error, { id: string; body: CreateExamFromDocumentBody }> {
  return useMutation<DocumentExamResult, Error, { id: string; body: CreateExamFromDocumentBody }>({
    mutationFn: ({ id, body }) => documentService.createExam(id, body),
  });
}

export function useReparseDocumentMutation(): UseMutationResult<SourceDocument, Error, { id: string; body: ReparseDocumentBody }> {
  const qc = useQueryClient();
  return useMutation<SourceDocument, Error, { id: string; body: ReparseDocumentBody }>({
    mutationFn: ({ id, body }) => documentService.reparse(id, body),
    onSuccess: () => invalidate(qc, ...TOUCHED),
  });
}
