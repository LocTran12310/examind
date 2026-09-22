"use client";

import { useDefaultLayout } from "react-resizable-panels";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { splitStorage } from "@/lib/common/split-storage";

/**
 * Table on top, "Chi tiết" below, with a draggable divider. The split is remembered
 * per screen (`id`). Without a detail the table takes the whole height.
 */
export function MasterDetail({ id, master, detail }: { id: string; master: React.ReactNode; detail?: React.ReactNode | null }) {
  const { defaultLayout, onLayoutChanged } = useDefaultLayout({ id: `examind.split.${id}`, storage: splitStorage() });
  // One group whatever the state, so selecting the first row does not remount (and refetch) the table.
  return (
    <ResizablePanelGroup orientation="vertical" defaultLayout={detail ? defaultLayout : undefined} onLayoutChanged={detail ? onLayoutChanged : undefined}>
      <ResizablePanel id="master" defaultSize={detail ? "58" : "100"} minSize="25" className="min-h-0">
        <div className="h-full">{master}</div>
      </ResizablePanel>
      {detail && <ResizableHandle withHandle aria-label="Kéo để đổi chiều cao" className="my-1 bg-transparent" />}
      {detail && (
        <ResizablePanel id="detail" defaultSize="42" minSize="15" className="min-h-0">
          <section aria-label="Chi tiết" className="h-full overflow-auto">
            {detail}
          </section>
        </ResizablePanel>
      )}
    </ResizablePanelGroup>
  );
}
