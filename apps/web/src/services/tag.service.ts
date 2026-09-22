import type { SearchBody } from "@/dtos/search.dto";
import type { CreateTagBody, UpdateTagBody } from "@/dtos/tag.dto";
import type { SearchPage } from "@/interfaces/search-page.interface";
import type { Tag } from "@/interfaces/tag.interface";
import { http } from "@/lib/common/http";

export const tagService = {
  search: (body: SearchBody) => http<SearchPage<Tag>>("/tags/search", { body }),
  create: (body: CreateTagBody) => http<Tag>("/tags", { body }),
  update: (id: string, body: UpdateTagBody) => http<Tag>(`/tags/${id}`, { method: "PATCH", body }),
  remove: (id: string) => http<void>(`/tags/${id}`, { method: "DELETE" }),
};
