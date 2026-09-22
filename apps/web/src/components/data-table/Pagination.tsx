"use client";

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PAGE_SIZES } from "./useTableQuery";

const n = (x: number) => x.toLocaleString("vi-VN");

/**
 * « ‹ Trang [n] trên N › » · size · "Hiển thị a–b trên T kết quả".
 * Sized by its container (not the viewport) so it also fits narrow panels: labels, first/last
 * buttons and the long summary drop out step by step.
 */
export function Pagination({
  page,
  pageSize,
  total,
  onPage,
  onPageSize,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPage: (p: number) => void;
  onPageSize?: (s: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const [draft, setDraft] = useState(String(page));
  useEffect(() => setDraft(String(page)), [page]);
  const from = total ? (page - 1) * pageSize + 1 : 0;
  const to = Math.min(total, page * pageSize);
  const go = (p: number) => onPage(Math.min(pages, Math.max(1, p)));
  return (
    <div className="@container">
      <nav aria-label="Phân trang" className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 py-2 text-sm">
        <div className="flex min-w-0 items-center gap-1">
          <Button variant="outline" size="icon-sm" aria-label="Trang đầu" className="hidden @sm:inline-flex" disabled={page <= 1} onClick={() => go(1)}>
            <ChevronsLeft />
          </Button>
          <Button variant="outline" size="icon-sm" aria-label="Trang trước" disabled={page <= 1} onClick={() => go(page - 1)}>
            <ChevronLeft />
          </Button>
          <span className="hidden px-1 text-muted-foreground @lg:inline">Trang</span>
          <Input
            aria-label="Số trang"
            className="h-7 w-12 px-1 text-center"
            inputMode="numeric"
            value={draft}
            onChange={(e) => setDraft(e.target.value.replace(/\D/g, ""))}
            onKeyDown={(e) => e.key === "Enter" && go(Number(draft) || 1)}
            onBlur={() => Number(draft) !== page && go(Number(draft) || 1)}
          />
          <span className="px-1 whitespace-nowrap text-muted-foreground">
            <span className="@lg:hidden">/ {n(pages)}</span>
            <span className="hidden @lg:inline">trên {n(pages)}</span>
          </span>
          <Button variant="outline" size="icon-sm" aria-label="Trang sau" disabled={page >= pages} onClick={() => go(page + 1)}>
            <ChevronRight />
          </Button>
          <Button variant="outline" size="icon-sm" aria-label="Trang cuối" className="hidden @sm:inline-flex" disabled={page >= pages} onClick={() => go(pages)}>
            <ChevronsRight />
          </Button>
          {onPageSize && (
            <Select value={String(pageSize)} onValueChange={(v) => onPageSize(Number(v))}>
              <SelectTrigger size="sm" className="ml-1 w-18" aria-label="Số dòng mỗi trang">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PAGE_SIZES.map((s) => (
                  <SelectItem key={s} value={String(s)}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
        <div className="ml-auto text-xs whitespace-nowrap text-muted-foreground @xl:text-sm" aria-live="polite">
          <span className="@2xl:hidden">
            {n(from)}–{n(to)} / {n(total)}
          </span>
          <span className="hidden @2xl:inline">
            Hiển thị {n(from)}–{n(to)} trên {n(total)} kết quả
          </span>
        </div>
      </nav>
    </div>
  );
}
