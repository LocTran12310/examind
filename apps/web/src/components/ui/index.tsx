"use client";

import clsx from "clsx";
import { forwardRef, useEffect, useRef } from "react";

type BtnVariant = "primary" | "secondary" | "ghost" | "danger";

export const Button = forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: BtnVariant; size?: "sm" | "md" }
>(function Button({ variant = "secondary", size = "md", className, ...props }, ref) {
  return (
    <button
      ref={ref}
      className={clsx(
        "inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition disabled:opacity-50 disabled:cursor-not-allowed",
        size === "sm" ? "h-8 px-2.5 text-sm" : "h-9 px-3.5 text-sm",
        variant === "primary" && "bg-brand-600 text-white hover:bg-brand-700",
        variant === "secondary" && "border border-gray-300 bg-white hover:bg-gray-50",
        variant === "ghost" && "hover:bg-gray-100",
        variant === "danger" && "border border-red-300 bg-white text-red-700 hover:bg-red-50",
        className,
      )}
      {...props}
    />
  );
});

export const Input = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }>(
  function Input({ className, invalid, ...props }, ref) {
    return (
      <input
        ref={ref}
        aria-invalid={invalid || undefined}
        className={clsx(
          "h-9 w-full rounded-md border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-brand-100",
          invalid ? "border-red-400" : "border-gray-300 focus:border-brand-500",
          className,
        )}
        {...props}
      />
    );
  },
);

export function Select({ className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={clsx("h-9 rounded-md border border-gray-300 bg-white px-2 text-sm outline-none focus:border-brand-500", className)}
      {...props}
    />
  );
}

export const Textarea = forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(function Textarea({ className, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      className={clsx("w-full rounded-md border border-gray-300 bg-white p-2 text-sm outline-none focus:border-brand-500", className)}
      {...props}
    />
  );
});

export function Field({ label, error, children, hint }: { label: string; error?: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      {children}
      {hint && !error && <span className="block text-xs text-gray-500">{hint}</span>}
      {error && <span className="block text-xs text-red-600">{error}</span>}
    </label>
  );
}

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx("rounded-xl border border-gray-200 bg-white p-5", className)} {...props} />;
}

export function Badge({ tone = "gray", children }: { tone?: "gray" | "green" | "red" | "amber" | "blue"; children: React.ReactNode }) {
  const tones = {
    gray: "bg-gray-100 text-gray-700",
    green: "bg-green-50 text-green-700",
    red: "bg-red-50 text-red-700",
    amber: "bg-amber-50 text-amber-800",
    blue: "bg-brand-50 text-brand-700",
  };
  return <span className={clsx("inline-flex rounded px-2 py-0.5 text-xs font-medium", tones[tone])}>{children}</span>;
}

export function Alert({ tone = "red", children }: { tone?: "red" | "green" | "amber" | "blue"; children: React.ReactNode }) {
  const tones = {
    red: "border-red-200 bg-red-50 text-red-800",
    green: "border-green-200 bg-green-50 text-green-800",
    amber: "border-amber-200 bg-amber-50 text-amber-900",
    blue: "border-brand-100 bg-brand-50 text-brand-700",
  };
  return (
    <div role="alert" className={clsx("rounded-md border px-3 py-2 text-sm", tones[tone])}>
      {children}
    </div>
  );
}

export function PageHeader({ title, actions, subtitle }: { title: string; subtitle?: string; actions?: React.ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}

export function Modal({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal?.();
    if (!open && d.open) d.close?.();
  }, [open]);
  if (!open) return null;
  return (
    <dialog
      ref={ref}
      open={typeof HTMLDialogElement === "undefined" || !HTMLDialogElement.prototype.showModal ? true : undefined}
      onClose={onClose}
      onCancel={onClose}
      aria-label={title}
      className={clsx("m-auto w-full rounded-xl p-0 backdrop:bg-black/40", wide ? "max-w-3xl" : "max-w-lg")}
    >
      <div className="flex items-center justify-between border-b px-5 py-3">
        <h2 className="font-semibold">{title}</h2>
        <button aria-label="Đóng" className="text-gray-500 hover:text-gray-800" onClick={onClose}>
          ✕
        </button>
      </div>
      <div className="p-5">{children}</div>
    </dialog>
  );
}

export const th = "px-3 py-2 text-left text-xs font-medium uppercase tracking-wide text-gray-500";
export const td = "px-3 py-2 text-sm";

export function Table({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
      <table className="w-full divide-y divide-gray-100">{children}</table>
    </div>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500">{children}</div>;
}

export function CopyButton({ text, label = "Sao chép" }: { text: string; label?: string }) {
  return (
    <Button size="sm" type="button" onClick={() => navigator.clipboard?.writeText(text)}>
      {label}
    </Button>
  );
}
