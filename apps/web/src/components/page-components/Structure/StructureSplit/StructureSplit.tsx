"use client";

import { useDefaultLayout } from "react-resizable-panels";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { splitStorage } from "@/lib/common/split-storage";
import { useIsMobile } from "@/hooks/use-mobile";

/** Tree | table side by side with a draggable divider on desktop; stacked on phones. */
export function StructureSplit({ tree, title, crumbs, action, children }: { tree: React.ReactNode; title: string; crumbs?: string; action?: React.ReactNode; children: React.ReactNode }) {
  const mobile = useIsMobile();
  const { defaultLayout, onLayoutChanged } = useDefaultLayout({ id: "examind.split.structure", storage: splitStorage() });
  const treeCard = (
    <Card className="h-full min-h-0 overflow-auto py-3">
      <CardContent className="px-3">{tree}</CardContent>
    </Card>
  );
  const main = (
    <Card className="flex h-full min-h-0 min-w-0 flex-col gap-3 py-4">
      <CardHeader className="px-4">
        <CardTitle>{title}</CardTitle>
        {crumbs && <CardDescription>{crumbs}</CardDescription>}
        {action && <CardAction>{action}</CardAction>}
      </CardHeader>
      {/* the panel is handed a height and fills it; this box does NOT scroll. A table inside only keeps its
          toolbar, its sticky header and its pagination still when it owns the scrolling itself — if this box
          scrolled instead, all three would ride away with the rows. */}
      <CardContent className="flex min-h-0 flex-1 flex-col px-4">{children}</CardContent>
    </Card>
  );
  if (mobile)
    return (
      <div className="grid gap-4">
        {treeCard}
        {main}
      </div>
    );
  return (
    <ResizablePanelGroup orientation="horizontal" defaultLayout={defaultLayout} onLayoutChanged={onLayoutChanged}>
      <ResizablePanel id="tree" defaultSize="28" minSize="18" maxSize="50" className="min-w-0">
        {treeCard}
      </ResizablePanel>
      <ResizableHandle withHandle aria-label="Kéo để đổi độ rộng" className="mx-1 bg-transparent" />
      <ResizablePanel id="main" defaultSize="72" minSize="40" className="min-w-0">
        {main}
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
