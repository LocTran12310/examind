import { AlertCircle, CheckCircle2, Info, TriangleAlert } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

type Kind = "error" | "success" | "warning" | "info";
const ICON = { error: AlertCircle, success: CheckCircle2, warning: TriangleAlert, info: Info };
const CLS: Record<Kind, string> = {
  error: "",
  success: "border-emerald-500/30 text-emerald-700 dark:text-emerald-400 *:data-[slot=alert-description]:text-emerald-700 dark:*:data-[slot=alert-description]:text-emerald-400",
  warning: "border-amber-500/30 text-amber-800 dark:text-amber-400 *:data-[slot=alert-description]:text-amber-800 dark:*:data-[slot=alert-description]:text-amber-400",
  info: "",
};

/** shadcn Alert with an icon per kind; `error` uses the destructive variant. */
export function FormAlert({ kind = "error", className, children }: { kind?: Kind; className?: string; children: React.ReactNode }) {
  const Icon = ICON[kind];
  return (
    <Alert variant={kind === "error" ? "destructive" : "default"} className={cn(CLS[kind], className)}>
      <Icon />
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  );
}
