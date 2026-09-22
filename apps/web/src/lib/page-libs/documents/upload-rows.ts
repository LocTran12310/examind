import type { DuplicateCheck, DuplicateChoice, SourceDocument } from "@/interfaces/document.interface";

/** One file of an upload batch. */
export interface UploadRow {
  file: File;
  state: "checking" | "waiting" | "sending" | "queued" | "duplicate" | "replaced" | "skipped" | "error";
  message?: string;
  doc?: SourceDocument;
  conflict?: DuplicateCheck;
  choice?: DuplicateChoice;
}

/** Hex SHA-256 of a file's content, computed in the browser. */
export async function sha256(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  const hash = await crypto.subtle.digest("SHA-256", buf);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Default: the same content is skipped; a new version of a same-name file replaces the newest one. */
export const defaultChoice = (c: DuplicateCheck): DuplicateChoice | undefined => (c.same_file ? "skip" : c.same_name.length ? "replace" : undefined);

/** A conflicting row the user chose to skip: settled without a request. */
export const skipped = (r: UploadRow) => !!r.conflict && r.choice === "skip";

export function stateLabel(r: UploadRow): string {
  switch (r.state) {
    case "checking":
      return "Đang kiểm tra…";
    case "waiting":
      return skipped(r) ? "Sẽ bỏ qua" : "Chờ tải lên";
    case "replaced":
      return "Đã ghi đè — đang tách lại";
    case "skipped":
      return "Đã bỏ qua";
    case "sending":
      return "Đang tải…";
    case "queued":
      return "Đã đưa vào hàng đợi";
    case "duplicate":
      return "Đã có — dùng bản cũ";
    default:
      return r.message ?? "Lỗi";
  }
}

/** The choices offered for a conflicting file. */
export function choiceOptions(c: DuplicateCheck): { value: DuplicateChoice; label: string }[] {
  return c.same_file
    ? [
        { value: "skip", label: "Bỏ qua (dùng bản đã có)" },
        { value: "replace", label: "Tách lại bản đã có" },
      ]
    : [
        { value: "replace", label: "Ghi đè bản cũ" },
        { value: "keep_both", label: "Giữ cả hai" },
        { value: "skip", label: "Bỏ qua file này" },
      ];
}
