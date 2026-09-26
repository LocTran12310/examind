"use client";

import { Upload, X } from "lucide-react";
import { useId, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const UNITS = ["B", "KB", "MB", "GB"];

/** Bytes as a short label with a Vietnamese decimal comma: `820 B`, `12,4 KB`, `1,1 MB`. */
export function formatFileSize(bytes: number): string {
  let n = bytes, unit = 0;
  for (; n >= 1024 && unit < UNITS.length - 1; unit++) n /= 1024;
  return `${unit === 0 ? Math.round(n) : (Math.round(n * 10) / 10).toFixed(1).replace(".", ",")} ${UNITS[unit]}`;
}

const extensions = (accept: string) => accept.split(",").map((e) => e.trim().toLowerCase()).filter(Boolean);

export interface FileDropFieldProps {
  label: string;
  /** Extensions, as the `accept` attribute wants them: `".csv,.xlsx"`. Anything else is refused. */
  accept: string;
  value: File | null;
  onChange: (file: File | null) => void;
  hint?: React.ReactNode;
  /** Shown under the zone next to the refusal message — the template link belongs here. */
  children?: React.ReactNode;
  disabled?: boolean;
  /** The input gets it as is, the zone gets `<testId>-zone`. */
  testId?: string;
  className?: string;
}

/**
 * One file, chosen by a click, the keyboard or a drag-and-drop onto the bordered zone. The input stays in the
 * page (`sr-only`, so tab reaches it and a phone opens its picker); the zone shows the focus ring for it.
 */
export function FileDropField({ label, accept, value, onChange, hint, children, disabled, testId, className }: FileDropFieldProps) {
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);
  const exts = extensions(accept);
  const list = exts.join(", ");

  const take = (file: File | undefined) => {
    if (input.current) input.current.value = "";
    if (!file) return;
    if (!exts.some((e) => file.name.toLowerCase().endsWith(e))) {
      setRefused(`Chỉ nhận file ${list}. File “${file.name}” không đúng định dạng.`);
      return onChange(null);
    }
    setRefused(null);
    onChange(file);
  };
  const clear = () => {
    if (input.current) input.current.value = "";
    setRefused(null);
    onChange(null);
  };

  return (
    <div className={cn("grid gap-1.5", className)}>
      <input
        ref={input}
        id={id}
        data-testid={testId}
        type="file"
        accept={accept}
        disabled={disabled}
        aria-describedby={`${id}-msg`}
        className="peer sr-only"
        onChange={(e) => take(e.target.files?.[0])}
      />
      <div
        data-testid={testId && `${testId}-zone`}
        onDragOver={(e) => (e.preventDefault(), setDrag(!disabled))}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          if (!disabled) take(e.dataTransfer?.files?.[0]);
        }}
        className={cn(
          "rounded-xl border-2 border-dashed transition-colors peer-focus-visible:border-ring peer-focus-visible:ring-3 peer-focus-visible:ring-ring/50",
          refused ? "border-destructive" : drag ? "border-primary bg-primary/10" : "border-input",
          disabled && "opacity-50",
        )}
      >
        <label htmlFor={id} className={cn("flex flex-col items-center gap-1 px-4 py-6 text-center text-sm", disabled ? "cursor-not-allowed" : "cursor-pointer")}>
          <Upload className="size-5 text-muted-foreground" />
          <span className="font-medium">{label}</span>
          <span className="text-muted-foreground">Bấm để chọn file, hoặc kéo thả file vào đây</span>
          <span className="text-xs text-muted-foreground/80">Định dạng: {list}</span>
        </label>
        {value && (
          <div className="flex items-center gap-2 border-t px-3 py-2 text-sm" data-testid={testId && `${testId}-chosen`}>
            <span className="min-w-0 flex-1 truncate" title={value.name}>
              {value.name}
            </span>
            <span className="shrink-0 text-xs text-muted-foreground">{formatFileSize(value.size)}</span>
            <Button type="button" variant="ghost" size="icon-xs" aria-label={`Bỏ file ${value.name}`} disabled={disabled} onClick={clear}>
              <X />
            </Button>
          </div>
        )}
      </div>
      <div id={`${id}-msg`} className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
        {refused ? <span className="text-destructive">{refused}</span> : hint ? <span className="text-muted-foreground">{hint}</span> : null}
        {children}
      </div>
    </div>
  );
}
