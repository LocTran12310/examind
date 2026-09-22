/** Body of `POST /<resource>/search` (architecture-refactor ADR-03). */
export interface SearchFilter {
  operator?: string;
  value?: string | number | boolean | (string | number)[] | null;
  from?: string | number;
  to?: string | number;
}

export interface SearchSort {
  field: string;
  desc?: boolean;
}

export interface SearchBody {
  page: number;
  limit: number;
  q?: string;
  sort?: SearchSort[];
  filters?: Record<string, SearchFilter>;
  [param: string]: unknown;
}
