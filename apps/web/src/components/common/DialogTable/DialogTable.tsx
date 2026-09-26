"use client";

import { ChevronDown } from "lucide-react";
import { createContext, useContext } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

/** One content column. The checkbox and the fold arrow are not columns: the table draws them itself, so the cells
 *  of a row line up with this list one for one — parent rows and folded child rows alike. */
export interface DialogTableColumn {
  header?: React.ReactNode;
  /** goes on the head and on every cell, so a width, an alignment or `whitespace-normal` is written once */
  className?: string;
  /** dropped below `sm`: three text columns plus a button do not fit a 390 px phone, and a column that is cut in
   *  half is worse than one that is not there — the row carries what is dropped under its first cell instead */
  hideOnPhone?: boolean;
}

type Frame = { columns: DialogTableColumn[]; selectable: boolean; foldable: boolean };
const FRAME = createContext<Frame>({ columns: [], selectable: false, foldable: false });

/** The table the two "Thêm học sinh" dialogs are both made of: a header that stays while only the body scrolls,
 *  rows that may fold open over their children, and a leading checkbox column.
 *
 *  It is deliberately not `DataTable`: that one owns URL state, server paging, filters and a toolbar, none of
 *  which a picker inside a dialog wants. The scroll box fills its flex parent instead of carrying a `max-h`, so
 *  the dialog keeps one height and the buttons under it stay where the cursor left them however many rows arrive. */
export function DialogTable({
  columns,
  selectable = false,
  foldable = false,
  testId,
  children,
}: {
  columns: DialogTableColumn[];
  selectable?: boolean;
  foldable?: boolean;
  testId?: string;
  children: React.ReactNode;
}) {
  return (
    <FRAME.Provider value={{ columns, selectable, foldable }}>
      {/* the table's own x-scroll wrapper is turned off so the header sticks to this box, as in DataTable */}
      <div data-slot="dialog-table" className="min-h-0 flex-1 overflow-auto rounded-lg border [&>[data-slot=table-container]]:overflow-visible">
        <Table data-testid={testId}>
          <TableHeader className="sticky top-0 z-10 bg-card shadow-[inset_0_-1px_0_var(--border)]">
            <TableRow className="hover:bg-transparent">
              {selectable && <TableHead className="w-8" />}
              {foldable && <TableHead className="w-8" />}
              {columns.map((c, i) => (
                <TableHead key={i} className={cn(c.className, c.hideOnPhone && "max-sm:hidden")}>
                  {c.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>{children}</TableBody>
        </Table>
      </div>
    </FRAME.Provider>
  );
}

/** One row of a `DialogTable`, and — while it is folded open — whatever rows are nested inside it. A row is a
 *  component rather than a plain object because a folded row loads its own children (one class, one roster). */
export function DialogTableRow({
  cells,
  select,
  fold,
  muted,
  span,
  children,
}: {
  /** one per column of the table; a missing one leaves the cell empty */
  cells: React.ReactNode[];
  select?: { checked: boolean; disabled?: boolean; label: string; onChange: () => void };
  fold?: { open: boolean; label: string; onToggle: () => void };
  muted?: boolean;
  /** the whole row is the first cell: a line like "Đang tải…" or "chưa có lớp nào", not a record */
  span?: boolean;
  /** rows shown under this one while `fold.open` */
  children?: React.ReactNode;
}) {
  const { columns, selectable, foldable } = useContext(FRAME);
  return (
    <>
      <TableRow className={cn(muted && "bg-muted/40")}>
        {selectable && (
          <TableCell>
            {select && <Checkbox aria-label={select.label} checked={select.checked} disabled={select.disabled} onCheckedChange={select.onChange} />}
          </TableCell>
        )}
        {foldable && (
          <TableCell>
            {fold && (
              <button
                type="button"
                aria-label={fold.label}
                aria-expanded={fold.open}
                onClick={fold.onToggle}
                className="flex items-center text-muted-foreground hover:text-foreground"
              >
                <ChevronDown className={cn("size-4 transition-transform", fold.open && "rotate-180")} />
              </button>
            )}
          </TableCell>
        )}
        {span ? (
          <TableCell colSpan={columns.length} className="text-muted-foreground">
            {cells[0]}
          </TableCell>
        ) : (
          columns.map((c, i) => (
            <TableCell key={i} className={cn(c.className, c.hideOnPhone && "max-sm:hidden")}>
              {cells[i]}
            </TableCell>
          ))
        )}
      </TableRow>
      {fold?.open && children}
    </>
  );
}
