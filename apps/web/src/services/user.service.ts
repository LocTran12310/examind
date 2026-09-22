import type { SearchBody } from "@/dtos/search.dto";
import type { CreateUserBody, ImportCommitBody, LinkUserBody, UpdateUserBody } from "@/dtos/user.dto";
import type { SearchPage } from "@/interfaces/search-page.interface";
import type { Credential, ImportCommitted, ImportPreview, User, UserCreated } from "@/interfaces/user.interface";
import { http } from "@/lib/common/http";

export const userService = {
  /** Users of the org (a teacher sees students only); `class_id` narrows to one class. */
  search: (body: SearchBody) => http<SearchPage<User>>("/users/search", { body }),
  get: (id: string) => http<User>(`/users/${id}`),
  create: (body: CreateUserBody) => http<UserCreated>("/users", { body }),
  update: (id: string, body: UpdateUserBody) => http<User>(`/users/${id}`, { method: "PATCH", body }),
  resetPassword: (id: string) => http<Credential>(`/users/${id}/reset-password`, { method: "POST" }),
  link: (body: LinkUserBody) => http<User>("/users/link", { body }),
  /** Remove an account of another org from this org (its home org keeps it). */
  unlink: (id: string) => http<void>(`/users/${id}/membership`, { method: "DELETE" }),
  importPreview: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return http<ImportPreview>("/users/import/preview", { form });
  },
  importCommit: (body: ImportCommitBody) => http<ImportCommitted>("/users/import/commit", { body }),
};
