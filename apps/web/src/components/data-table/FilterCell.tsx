"use client";

import { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { FilterSpec } from "./types";

export const DEBOUNCE_MS = 300;
const ALL = "__all";

/** Text input that writes to the URL after a pause; follows the URL when it changes elsewhere (Back). */
function DebouncedInput({ value, onChange, ...props }: { value: string; onChange: (v: string) => void } & Omit<React.ComponentProps<typeof Input>, "value" | "onChange">) {
  const [draft, setDraft] = useState(value);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const last = useRef(value);
  useEffect(() => {
    if (value !== last.current) {
      last.current = value;
      setDraft(value);
    }
  }, [value]);
  useEffect(() => () => void (timer.current && clearTimeout(timer.current)), []);
  return (
    <Input
      {...props}
      value={draft}
      onChange={(e) => {
        const v = e.target.value;
        setDraft(v);
        if (timer.current) clearTimeout(timer.current);
        timer.current = setTimeout(() => {
          last.current = v;
          onChange(v);
        }, DEBOUNCE_MS);
      }}
    />
  );
}

export function FilterCell({ spec, name, label, get, set }: { spec: FilterSpec; name: string; label: string; get: (k: string) => string; set: (changes: Record<string, string | null>) => void }) {
  const key = spec.key ?? name;
  const cls = "h-7 text-xs font-normal";
  switch (spec.kind) {
    case "text":
      return <DebouncedInput aria-label={`Lọc ${label}`} className={cls} placeholder={spec.placeholder ?? "Giá trị…"} value={get(key)} onChange={(v) => set({ [key]: v || null })} />;
    case "number":
      return <DebouncedInput aria-label={`Lọc ${label}`} className={cls} inputMode="numeric" placeholder="=" value={get(key)} onChange={(v) => set({ [key]: v.replace(/[^\d.-]/g, "") || null })} />;
    case "select":
      return (
        <Select value={get(key) || ALL} onValueChange={(v) => set({ [key]: v === ALL ? null : v })}>
          <SelectTrigger size="sm" aria-label={`Lọc ${label}`} className={`${cls} w-full`}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Tất cả</SelectItem>
            {spec.options.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    case "date":
      return (
        <div className="flex items-center gap-1">
          <Input type="date" aria-label={`${label} từ ngày`} className={`${cls} min-w-0 px-1`} value={get(`${key}_from`)} onChange={(e) => set({ [`${key}_from`]: e.target.value || null })} />
          <span className="text-muted-foreground">–</span>
          <Input type="date" aria-label={`${label} đến ngày`} className={`${cls} min-w-0 px-1`} value={get(`${key}_to`)} onChange={(e) => set({ [`${key}_to`]: e.target.value || null })} />
        </div>
      );
  }
}
