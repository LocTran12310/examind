import { ApiError } from "@/lib/common/http";

/** Field errors and a message from a failed mutation (`details.fields` of the error body). */
export function formErrors(error: unknown): { fields: Record<string, string>; message: string | null } {
  if (!error) return { fields: {}, message: null };
  if (error instanceof ApiError) return { fields: error.fields ?? {}, message: error.message };
  return { fields: {}, message: "Có lỗi xảy ra" };
}
