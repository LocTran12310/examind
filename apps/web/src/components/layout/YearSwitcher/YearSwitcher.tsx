"use client";

import { CalendarRange } from "lucide-react";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { YEAR_STATUS_LABEL } from "@/constants/school-year.constant";
import { useYear } from "@/hooks/common/use-year";

/** Header school year (staff); the choice is kept per org in this browser. */
export function YearSwitcher() {
  const { years, year, setYear } = useYear();
  if (!years.length || !year) return null;
  return (
    <Select value={year.id} onValueChange={setYear}>
      <SelectTrigger aria-label="Chọn năm học" className="w-auto gap-1.5 px-2 sm:gap-2">
        <CalendarRange className="hidden text-muted-foreground sm:block" />
        {/* the trigger shows the code only; the list shows the status badges */}
        <SelectValue>{year.code}</SelectValue>
      </SelectTrigger>
      <SelectContent align="end">
        {years.map((y) => (
          <SelectItem key={y.id} value={y.id}>
            {y.code}
            {y.status !== "planning" && (
              <ToneBadge tone={y.status === "active" ? "green" : "gray"} className="ml-1">
                {YEAR_STATUS_LABEL[y.status]}
              </ToneBadge>
            )}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
