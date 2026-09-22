"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** The back-office-style action bar above a table (navy in light mode, like the sidebar). */
export function Toolbar({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div role="toolbar" aria-label="Thao tác" className={cn("toolbar-bar flex flex-wrap items-center gap-0.5 rounded-t-lg px-2 py-1.5", className)}>
      {children}
    </div>
  );
}

export function ToolbarButton({ className, ...props }: React.ComponentProps<typeof Button>) {
  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn("text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground disabled:opacity-40", className)}
      {...props}
    />
  );
}

export function ToolbarSeparator() {
  return <span aria-hidden className="mx-1 h-5 w-px bg-sidebar-border" />;
}
