"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

const NONE = "__none";

export interface Option {
  value: string;
  label: React.ReactNode;
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
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
