import { cn } from "@/lib/utils";

/** A padded surface for page sections (shadcn `Card` tokens, without the Card header/content structure). */
export function Panel({ className, ...props }: React.ComponentProps<"section">) {
  return <section data-slot="panel" className={cn("rounded-xl border bg-card p-5 text-card-foreground", className)} {...props} />;
}
