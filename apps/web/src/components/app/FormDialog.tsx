"use client";

import { Maximize2, Minimize2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

type Size = { w: number; h: number };
const MIN: Size = { w: 320, h: 180 };
const GAP = 16; // keep the dialog this far from the window edges

/** Edges and corners that resize the dialog: x/y say which way the size grows. */
const HANDLES: { name: string; x: -1 | 0 | 1; y: -1 | 0 | 1; className: string }[] = [
  { name: "phải", x: 1, y: 0, className: "top-3 -right-1 bottom-3 w-2 cursor-ew-resize" },
  { name: "trái", x: -1, y: 0, className: "top-3 -left-1 bottom-3 w-2 cursor-ew-resize" },
  { name: "dưới", x: 0, y: 1, className: "-bottom-1 left-3 right-3 h-2 cursor-ns-resize" },
  { name: "trên", x: 0, y: -1, className: "-top-1 left-3 right-3 h-2 cursor-ns-resize" },
  { name: "góc dưới phải", x: 1, y: 1, className: "-right-1 -bottom-1 size-4 cursor-nwse-resize" },
  { name: "góc dưới trái", x: -1, y: 1, className: "-bottom-1 -left-1 size-4 cursor-nesw-resize" },
  { name: "góc trên phải", x: 1, y: -1, className: "-top-1 -right-1 size-4 cursor-nesw-resize" },
  { name: "góc trên trái", x: -1, y: -1, className: "-top-1 -left-1 size-4 cursor-nwse-resize" },
];

/** shadcn Dialog with the header every form dialog uses, plus "Phóng to" (or double-click the title)
 *  and resizing from any edge or corner, like the back-office dialogs (ui-polish A-01). */
export function FormDialog({
  open,
  onOpenChange,
  title,
  description,
  wide,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: React.ReactNode;
  wide?: boolean;
  children: React.ReactNode;
}) {
  const [maximized, setMaximized] = useState(false);
  const [size, setSize] = useState<Size | null>(null);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) {
      setMaximized(false);
      setSize(null);
    }
  }, [open]);

  function startResize(e: React.PointerEvent, x: number, y: number) {
    const el = box.current;
    if (!el) return;
    e.preventDefault();
    e.stopPropagation();
    const r = el.getBoundingClientRect();
    const start = { px: e.clientX, py: e.clientY, w: r.width, h: r.height };
    setMaximized(false);
    const target = e.currentTarget as HTMLElement;
    target.setPointerCapture?.(e.pointerId);
    const move = (ev: PointerEvent) => {
      // the dialog is centred: an edge follows the pointer when the size changes by twice the move
      const w = x ? start.w + x * (ev.clientX - start.px) * 2 : start.w;
      const h = y ? start.h + y * (ev.clientY - start.py) * 2 : start.h;
      setSize({
        w: Math.round(Math.min(Math.max(w, MIN.w), window.innerWidth - GAP)),
        h: Math.round(Math.min(Math.max(h, MIN.h), window.innerHeight - GAP)),
      });
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  const style: React.CSSProperties | undefined = maximized
    ? { width: `calc(100vw - ${GAP}px)`, height: `calc(100svh - ${GAP}px)`, maxWidth: "none", maxHeight: "none" }
    : size
      ? { width: size.w, height: size.h, maxWidth: "none", maxHeight: "none" }
      : undefined;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        ref={box}
        style={style}
        data-maximized={maximized || undefined}
        className={cn("flex max-h-[90svh] flex-col gap-0 p-0", wide ? "sm:max-w-3xl" : "sm:max-w-lg", (maximized || size) && "sm:max-w-none")}
      >
        <DialogHeader className="shrink-0 px-4 pt-4 pr-20 pb-3" onDoubleClick={() => setMaximized((m) => !m)}>
          <DialogTitle className="select-none">{title}</DialogTitle>
          {description ? <DialogDescription>{description}</DialogDescription> : <DialogDescription className="sr-only">{title}</DialogDescription>}
        </DialogHeader>
        <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon-sm" className="absolute top-2 right-10" aria-label={maximized ? "Thu nhỏ" : "Phóng to"} onClick={() => setMaximized((m) => !m)}>
              {maximized ? <Minimize2 /> : <Maximize2 />}
            </Button>
          </TooltipTrigger>
          <TooltipContent>{maximized ? "Thu nhỏ" : "Phóng to"}</TooltipContent>
        </Tooltip>
        </TooltipProvider>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4">{children}</div>
        {!maximized &&
          HANDLES.map((hd) => (
            <div
              key={hd.name}
              aria-hidden
              data-resize={hd.name}
              className={cn("absolute z-10 hidden touch-none sm:block", hd.className)}
              onPointerDown={(e) => startResize(e, hd.x, hd.y)}
            />
          ))}
      </DialogContent>
    </Dialog>
  );
}
