import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type Tone = "gray" | "green" | "red" | "amber" | "blue";

const TONES: Record<Tone, string> = {
  gray: "bg-muted text-muted-foreground",
  green: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  red: "bg-destructive/10 text-destructive",
  amber: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
  blue: "bg-primary/10 text-primary",
};

/** Status pill: shadcn Badge with a semantic colour that works in light and dark mode. */
export function ToneBadge({ tone = "gray", className, children }: { tone?: Tone; className?: string; children: React.ReactNode }) {
  return (
    <Badge variant="secondary" className={cn("border-transparent", TONES[tone], className)}>
      {children}
    </Badge>
  );
}
