"use client";

import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

const NONE = "__none";

export interface Option {
  value: string;
  label: React.ReactNode;
  /** options with the same group are listed under that heading, in first-seen order */
  group?: string;
  disabled?: boolean;
}

function grouped(options: Option[]): [string | undefined, Option[]][] {
  const out: [string | undefined, Option[]][] = [];
  for (const o of options) {
    const last = out[out.length - 1];
    if (last && last[0] === o.group) last[1].push(o);
    else out.push([o.group, [o]]);
  }
  return out;
}

/** how close to the end of the list asks for the next page */
const END = 48;

/**
 * shadcn Select driven by an options list. `""` is a valid value (shown as `emptyLabel`), which
 * Radix Select itself does not allow. With `onEndReached` the list scrolls inside the dropdown and asks
 * for the next page as it reaches the end (pickers-builder A-07); `loadingMore` says so while it loads.
 */
export function OptionSelect({
  value,
  onValueChange,
  options,
  emptyLabel,
  placeholder,
  className,
  size,
  disabled,
  onEndReached,
  loadingMore,
  ...aria
}: {
  value: string;
  onValueChange: (v: string) => void;
  options: Option[];
  emptyLabel?: string;
  placeholder?: string;
  className?: string;
  size?: "sm" | "default";
  disabled?: boolean;
  /** the list is longer than what was loaded: called when scrolling reaches the end */
  onEndReached?: () => void;
  loadingMore?: boolean;
  id?: string;
  "aria-label"?: string;
  "aria-invalid"?: boolean;
  "aria-describedby"?: string;
}) {
  const items = (
    <>
      {emptyLabel !== undefined && <SelectItem value={NONE}>{emptyLabel}</SelectItem>}
      {grouped(options).map(([group, list], i) =>
        group ? (
          <SelectGroup key={`${group}-${i}`}>
            <SelectLabel>{group}</SelectLabel>
            {list.map((o) => (
              <SelectItem key={o.value} value={o.value} disabled={o.disabled}>
                {o.label}
              </SelectItem>
            ))}
          </SelectGroup>
        ) : (
          list.map((o) => (
            <SelectItem key={o.value} value={o.value} disabled={o.disabled}>
              {o.label}
            </SelectItem>
          ))
        ),
      )}
    </>
  );
  return (
    <Select value={value === "" ? (emptyLabel !== undefined ? NONE : undefined) : value} onValueChange={(v) => onValueChange(v === NONE ? "" : v)} disabled={disabled}>
      <SelectTrigger className={cn("w-full", className)} size={size} {...aria}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {onEndReached ? (
          <div
            data-testid="option-list"
            className="max-h-64 overflow-y-auto"
            onScroll={(e) => {
              const el = e.currentTarget;
              if (el.scrollTop + el.clientHeight >= el.scrollHeight - END) onEndReached();
            }}
          >
            {items}
            {loadingMore && <p className="px-2 py-1.5 text-xs text-muted-foreground">Đang tải thêm…</p>}
          </div>
        ) : (
          items
        )}
      </SelectContent>
    </Select>
  );
}
