import type { CheckDocumentsBody, CreateExamFromDocumentBody, ReparseDocumentBody, UpdateDocumentBody, UploadDocumentBody } from "@/dtos/document.dto";
import type { SearchBody } from "@/dtos/search.dto";
import type { DocumentExamResult, DuplicateCheck, SourceDocument, UploadResult } from "@/interfaces/document.interface";
import type { ParsedQuestion } from "@/interfaces/question.interface";
import type { SearchPage } from "@/interfaces/search-page.interface";
import { http } from "@/lib/common/http";

export const documentService = {
  search: (body: SearchBody) => http<SearchPage<SourceDocument>>("/documents/search", { body }),
  get: (id: string) => http<SourceDocument>(`/documents/${id}`),
  /** Which files are already here (same content) or share a name with an uploaded one. */
  check: (body: CheckDocumentsBody) => http<DuplicateCheck[]>("/documents/check", { body }),
  upload: ({ file, meta, config, on_duplicate, replace_id }: UploadDocumentBody) => {
    const form = new FormData();
    form.append("file", file);
    form.append("meta", JSON.stringify(meta));
    form.append("config", JSON.stringify(config));
    if (on_duplicate) form.append("on_duplicate", on_duplicate);
    if (replace_id) form.append("replace_id", replace_id);
    return http<UploadResult>("/documents", { form });
  },
  update: (id: string, body: UpdateDocumentBody) => http<SourceDocument>(`/documents/${id}`, { method: "PATCH", body }),
  remove: (id: string) => http<void>(`/documents/${id}`, { method: "DELETE" }),
  questions: (id: string) => http<ParsedQuestion[]>(`/documents/${id}/questions`),
  createExam: (id: string, body: CreateExamFromDocumentBody) => http<DocumentExamResult>(`/documents/${id}/exam`, { body }),
  reparse: (id: string, body: ReparseDocumentBody) => http<SourceDocument>(`/documents/${id}/reparse`, { body }),
  /** Link to download the original file. */
  fileUrl: (id: string) => `/api/documents/${id}/file`,
};
