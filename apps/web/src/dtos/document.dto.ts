import type { DocumentMeta, DuplicateChoice, ProcessingConfig } from "@/interfaces/document.interface";

/** One file probed by `POST /documents/check`. */
export interface FileProbe {
  name: string;
  size: number;
  sha256: string;
}

export interface CheckDocumentsBody {
  files: FileProbe[];
}

/** Multipart fields of `POST /documents`. */
export interface UploadDocumentBody {
  file: File;
  meta: DocumentMeta;
  config: Partial<ProcessingConfig>;
  on_duplicate?: DuplicateChoice;
  replace_id?: string;
}

export interface UpdateDocumentBody {
  meta: DocumentMeta;
}

export interface CreateExamFromDocumentBody {
  title?: string;
}

export interface ReparseDocumentBody {
  config?: ProcessingConfig;
}
