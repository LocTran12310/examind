"use client";

import { ChevronDown } from "lucide-react";
import { createContext, useContext } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Table, TableBody, TableCell, TableFooter, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { TABLE_CELL, TABLE_FOOT, TABLE_HEAD, TABLE_HEAD_ROW, TABLE_HEADER, TABLE_ROW, TABLE_SCROLL } from "@/constants/table.constant";
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
 *  It is deliberately not `DataTable` — that one owns URL state, server paging, filters and a toolbar, none of
 *  which a picker inside a dialog wants — but it must not *look* like a different table either: both take their
 *  header, rows, borders and scroll box from `constants/table.constant`, so the look has one source. The scroll
 *  box fills its flex parent instead of carrying a `max-h`, so the dialog keeps one height and the buttons under
 *  it stay where the cursor left them however many rows arrive.
 *
 *  `foot` is a row pinned to the bottom of that box: the line where the next entry is typed stays reachable
 *  without scrolling to it, and does not walk down the table as rows are added above it. */
export function DialogTable({
  columns,
  selectable = false,
  foldable = false,
  testId,
  foot,
  children,
}: {
  columns: DialogTableColumn[];
  selectable?: boolean;
  foldable?: boolean;
  testId?: string;
  /** a row pinned to the bottom of the scroll box, spanning every column */
  foot?: React.ReactNode;
  children: React.ReactNode;
}) {
  const span = columns.length + (selectable ? 1 : 0) + (foldable ? 1 : 0);
  return (
    <FRAME.Provider value={{ columns, selectable, foldable }}>
      <div data-slot="dialog-table" className={cn(TABLE_SCROLL, "rounded-lg border")}>
        <Table data-testid={testId}>
          <TableHeader className={TABLE_HEADER}>
            <TableRow className={TABLE_HEAD_ROW}>
              {selectable && <TableHead className={cn(TABLE_HEAD, "w-8")} />}
              {foldable && <TableHead className={cn(TABLE_HEAD, "w-8")} />}
              {columns.map((c, i) => (
                <TableHead key={i} className={cn(TABLE_HEAD, c.className, c.hideOnPhone && "max-sm:hidden")}>
                  {c.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>{children}</TableBody>
          {foot && (
            <TableFooter className={cn(TABLE_FOOT, "bg-card font-normal")} data-slot="dialog-table-foot">
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={span} className="p-2">
                  {foot}
                </TableCell>
              </TableRow>
            </TableFooter>
          )}
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
      <TableRow className={cn(TABLE_ROW, muted && "bg-muted/40 even:bg-muted/40")}>
        {selectable && (
          <TableCell className={TABLE_CELL}>
            {select && <Checkbox aria-label={select.label} checked={select.checked} disabled={select.disabled} onCheckedChange={select.onChange} />}
          </TableCell>
        )}
        {foldable && (
          <TableCell className={TABLE_CELL}>
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
          <TableCell colSpan={columns.length + (selectable ? 1 : 0) + (foldable ? 1 : 0)} className="text-muted-foreground">
            {cells[0]}
          </TableCell>
        ) : (
          columns.map((c, i) => (
            <TableCell key={i} className={cn(TABLE_CELL, c.className, c.hideOnPhone && "max-sm:hidden")}>
              {cells[i]}
            </TableCell>
          ))
        )}
      </TableRow>
      {fold?.open && children}
    </>
  );
}
