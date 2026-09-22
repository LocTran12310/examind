"use client";

import { useEffect, useRef, useState } from "react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuLabel, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { DatePicker, DateRangePicker } from "@/components/app/DatePicker";
import { Input } from "@/components/ui/input";
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput } from "@/components/ui/input-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { FilterSpec } from "./types";

export const DEBOUNCE_MS = 300;
const ALL = "__all";

/** Text input that writes to the URL after a pause; follows the URL when it changes elsewhere (Back). */
export function DebouncedInput({
  value,
  onChange,
  as: Field = Input,
  ...props
}: { value: string; onChange: (v: string) => void; as?: typeof Input } & Omit<React.ComponentProps<typeof Input>, "value" | "onChange">) {
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
    <Field
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

/** Operators of the header filters — the the reference symbols and labels (ui-standards ADR-01). */
export const TEXT_OPS = [
  { value: "*", label: "Chứa" },
  { value: "=", label: "Bằng" },
  { value: "+", label: "Bắt đầu bằng" },
  { value: "-", label: "Kết thúc bằng" },
  { value: "!", label: "Không chứa" },
] as const;
export const COMPARE_OPS = [
  { value: "=", label: "Bằng" },
  { value: "<", label: "Nhỏ hơn" },
  { value: "<=", label: "Nhỏ hơn hoặc bằng" },
  { value: ">", label: "Lớn hơn" },
  { value: ">=", label: "Lớn hơn hoặc bằng" },
] as const;
const RANGE = "range";
const SYMBOL: Record<string, string> = { "<=": "≤", ">=": "≥", [RANGE]: "↔" };
const symbol = (op: string) => SYMBOL[op] ?? op;

function OpMenu({ label, value, options, onChange }: { label: string; value: string; options: readonly { value: string; label: string }[]; onChange: (op: string) => void }) {
  const current = options.find((o) => o.value === value) ?? options[0];
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <InputGroupButton size="icon-xs" className="w-6 font-mono text-xs" aria-label={`Kiểu lọc ${label}: ${current.label}`} title={`${symbol(current.value)}: ${current.label}`}>
          {symbol(current.value)}
        </InputGroupButton>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-48">
        <DropdownMenuLabel className="text-xs">Chọn kiểu lọc</DropdownMenuLabel>
        <DropdownMenuRadioGroup value={current.value} onValueChange={onChange}>
          {options.map((o) => (
            <DropdownMenuRadioItem key={o.value} value={o.value} className="text-xs">
              <span className="w-5 font-mono">{symbol(o.value)}</span> {o.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/** One header filter. Values go to the URL as `<key>` (+ `<key>_op` when not the default), a date
 *  range as `<key>_from` / `<key>_to`; the server does the filtering. */
export function FilterCell({ spec, name, label, get, set }: { spec: FilterSpec; name: string; label: string; get: (k: string) => string; set: (changes: Record<string, string | null>) => void }) {
  const key = spec.key ?? name;
  const opKey = `${key}_op`;
  const cls = "h-7 text-xs font-normal";
  const group = "h-7 min-w-0 [&_input]:text-xs";
  switch (spec.kind) {
    case "text": {
      const op = get(opKey) || "*";
      return (
        <InputGroup className={group}>
          <InputGroupAddon align="inline-start" className="pl-0.5">
            <OpMenu label={label} value={op} options={TEXT_OPS} onChange={(v) => set({ [opKey]: v === "*" ? null : v })} />
          </InputGroupAddon>
          <DebouncedInput as={InputGroupInput} aria-label={`Lọc ${label}`} placeholder={spec.placeholder ?? "Giá trị…"} value={get(key)} onChange={(v) => set({ [key]: v || null })} />
        </InputGroup>
      );
    }
    case "number": {
      const op = get(opKey) || "=";
      return (
        <InputGroup className={group}>
          <InputGroupAddon align="inline-start" className="pl-0.5">
            <OpMenu label={label} value={op} options={COMPARE_OPS} onChange={(v) => set({ [opKey]: v === "=" ? null : v })} />
          </InputGroupAddon>
          <DebouncedInput as={InputGroupInput} aria-label={`Lọc ${label}`} inputMode="decimal" placeholder="Giá trị…" value={get(key)} onChange={(v) => set({ [key]: v.replace(/[^\d.,-]/g, "").replace(",", ".") || null })} />
        </InputGroup>
      );
    }
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
    case "date": {
      // a range by default (and for old links with _from/_to); pick = < ≤ > ≥ for a single day
      const op = get(opKey) || (get(key) ? "=" : RANGE);
      const choose = (v: string) => {
        const day = get(key) || get(`${key}_from`) || get(`${key}_to`) || null;
        if (v === RANGE) set({ [opKey]: null, [key]: null, [`${key}_from`]: day, [`${key}_to`]: null });
        else set({ [opKey]: v === "=" ? (day ? null : "=") : v, [key]: day, [`${key}_from`]: null, [`${key}_to`]: null });
      };
      const menu = <OpMenu label={label} value={op} options={[...COMPARE_OPS, { value: RANGE, label: "Trong khoảng" }]} onChange={choose} />;
      if (op === RANGE)
        return (
          <InputGroup className={group}>
            <InputGroupAddon align="inline-start" className="pl-0.5">
              {menu}
            </InputGroupAddon>
            <DateRangePicker
              size="sm"
              className="flex-1"
              triggerClassName="h-full border-0 bg-transparent shadow-none dark:bg-transparent"
              aria-label={`${label} trong khoảng`}
              from={get(`${key}_from`)}
              to={get(`${key}_to`)}
              onChange={(f, t) => set({ [`${key}_from`]: f || null, [`${key}_to`]: t || null })}
            />
          </InputGroup>
        );
      return (
          <div className="flex items-center gap-1">
            <InputGroup className={group}>
              <InputGroupAddon align="inline-start" className="pl-0.5">
                {menu}
              </InputGroupAddon>
              <DatePicker size="sm" className="flex-1" triggerClassName="h-full border-0 bg-transparent shadow-none dark:bg-transparent" aria-label={`${label} từ ngày`} value={get(`${key}_from`)} onChange={(d) => set({ [`${key}_from`]: d || null })} />
            </InputGroup>
            <span className="text-muted-foreground">–</span>
            <DatePicker size="sm" className="min-w-0 flex-1" aria-label={`${label} đến ngày`} value={get(`${key}_to`)} onChange={(d) => set({ [`${key}_to`]: d || null })} />
          </div>
        );
      return (
        <InputGroup className={group}>
          <InputGroupAddon align="inline-start" className="pl-0.5">
            {menu}
          </InputGroupAddon>
          <DatePicker size="sm" className="flex-1" triggerClassName="h-full border-0 bg-transparent shadow-none dark:bg-transparent" aria-label={`Lọc ${label}`} value={get(key)} onChange={(d) => set({ [key]: d || null, [opKey]: op === "=" ? null : op })} />
        </InputGroup>
      );
    }
  }
}
