import { cn } from "@/lib/utils";

/** A thin bar of a ratio (0–1): green from 80 %, amber from 50 %, red below. */
export function ScoreBar({ ratio }: { ratio: number }) {
  const pct = Math.round(ratio * 100);
  return (
    <div className="h-2 w-full overflow-hidden rounded bg-muted">
      <div className={cn("h-2", pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-amber-400" : "bg-red-400")} style={{ width: `${pct}%` }} />
    </div>
  );
}
