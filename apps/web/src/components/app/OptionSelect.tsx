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

/**
 * shadcn Select driven by an options list. `""` is a valid value (shown as `emptyLabel`), which
 * Radix Select itself does not allow.
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
  id?: string;
  "aria-label"?: string;
  "aria-invalid"?: boolean;
  "aria-describedby"?: string;
}) {
  return (
    <Select value={value === "" ? (emptyLabel !== undefined ? NONE : undefined) : value} onValueChange={(v) => onValueChange(v === NONE ? "" : v)} disabled={disabled}>
      <SelectTrigger className={cn("w-full", className)} size={size} {...aria}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {emptyLabel !== undefined && <SelectItem value={NONE}>{emptyLabel}</SelectItem>}
        {grouped(options).map(([group, items], i) =>
          group ? (
            <SelectGroup key={`${group}-${i}`}>
              <SelectLabel>{group}</SelectLabel>
              {items.map((o) => (
                <SelectItem key={o.value} value={o.value} disabled={o.disabled}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectGroup>
          ) : (
            items.map((o) => (
              <SelectItem key={o.value} value={o.value} disabled={o.disabled}>
                {o.label}
              </SelectItem>
            ))
          ),
        )}
      </SelectContent>
    </Select>
  );
}
