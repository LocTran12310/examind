"use client";

import { vi } from "date-fns/locale";
import { CalendarDays, X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { formatDate } from "@/lib/datetime";
import { cn } from "@/lib/utils";

/** `YYYY-MM-DD` ⇄ a local Date used only to draw the calendar (a calendar day has no time zone). */
const toDay = (v: string) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || "");
  return m ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : undefined;
};
const fromDay = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

/** shadcn date picker (Popover + Calendar) for a calendar day `YYYY-MM-DD`, shown dd/MM/yyyy. */
export function DatePicker({
  value,
  onChange,
  placeholder = "dd/mm/yyyy",
  clearable = true,
  size = "default",
  className,
  triggerClassName,
  id,
  disabled,
  "aria-label": ariaLabel,
  "aria-invalid": ariaInvalid,
  "aria-describedby": ariaDescribedby,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  clearable?: boolean;
  size?: "sm" | "default";
  className?: string;
  /** e.g. borderless inside an InputGroup */
  triggerClassName?: string;
  id?: string;
  disabled?: boolean;
  "aria-label"?: string;
  "aria-invalid"?: boolean;
  "aria-describedby"?: string;
}) {
  const [open, setOpen] = useState(false);
  const day = toDay(value);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <div className={cn("relative flex min-w-0 items-center", className)}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            id={id}
            disabled={disabled}
            aria-label={ariaLabel}
            aria-invalid={ariaInvalid}
            aria-describedby={ariaDescribedby}
            className={cn("w-full min-w-0 justify-start gap-1.5 px-2 font-normal", size === "sm" ? "h-7 text-xs" : "h-9", !value && "text-muted-foreground", clearable && value && "pr-7", triggerClassName)}
          >
            <CalendarDays className="size-3.5 shrink-0 opacity-60" />
            <span className="truncate">{value ? formatDate(value) : placeholder}</span>
          </Button>
        </PopoverTrigger>
        {clearable && value && !disabled && (
          <Button type="button" variant="ghost" size="icon-xs" className="absolute right-0.5 size-6" aria-label={`Xóa ${ariaLabel ?? "ngày"}`} onClick={() => onChange("")}>
            <X />
          </Button>
        )}
      </div>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          locale={vi}
          selected={day}
          defaultMonth={day}
          captionLayout="dropdown"
          onSelect={(d) => {
            if (d) onChange(fromDay(d));
            setOpen(false);
          }}
        />
      </PopoverContent>
    </Popover>
  );
}

/** Date + time in business time, same value as `datetime-local` (`YYYY-MM-DDTHH:mm`). */
export function DateTimePicker({
  value,
  onChange,
  id,
  "aria-label": ariaLabel,
  "aria-invalid": ariaInvalid,
  "aria-describedby": ariaDescribedby,
}: {
  value: string;
  onChange: (v: string) => void;
  id?: string;
  "aria-label"?: string;
  "aria-invalid"?: boolean;
  "aria-describedby"?: string;
}) {
  const [date, time = ""] = (value || "").split("T");
  const [draft, setDraft] = useState<string | null>(null);
  const commit = (t: string) => {
    const m = /^(\d{1,2}):?(\d{2})$/.exec(t.trim());
    if (!m || Number(m[1]) > 23 || Number(m[2]) > 59) return setDraft(null);
    setDraft(null);
    onChange(`${date || fromDay(new Date())}T${m[1].padStart(2, "0")}:${m[2]}`);
  };
  return (
    <div className="flex min-w-0 gap-1.5">
      <DatePicker
        id={id}
        aria-label={ariaLabel ? `${ariaLabel} — ngày` : undefined}
        aria-invalid={ariaInvalid}
        aria-describedby={ariaDescribedby}
        clearable={false}
        className="flex-1"
        value={date}
        onChange={(d) => onChange(d ? `${d}T${time || "07:00"}` : "")}
      />
      <Input
        aria-label={ariaLabel ? `${ariaLabel} — giờ` : "Giờ"}
        inputMode="numeric"
        placeholder="HH:mm"
        className="w-20 tabular-nums"
        value={draft ?? time}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={(e) => commit(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && commit((e.target as HTMLInputElement).value)}
      />
    </div>
  );
}
