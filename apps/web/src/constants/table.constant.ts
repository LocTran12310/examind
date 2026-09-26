/** One look for every table in the app, written once.
 *
 *  The list tables (`DataTable`) and the tables inside dialogs (`DialogTable`) are different machines — one owns
 *  URL state, server paging and filters, the other is a picker — but they must not be different *tables* to look
 *  at. Two copies of these class strings is two places for the look to drift, and drift is what makes a screen
 *  feel like it came from somewhere else. Change a line here and both follow. */

/** the only part that scrolls; the shadcn table's own x-scroll wrapper is turned off so the header can stick */
export const TABLE_SCROLL = "min-h-0 flex-1 overflow-auto [&>[data-slot=table-container]]:overflow-visible";
export const TABLE_HEADER = "sticky top-0 z-10 bg-card shadow-[inset_0_-1px_0_var(--border)]";
export const TABLE_HEAD_ROW = "bg-muted/40 hover:bg-muted/40";
/** the filter row under the headings. Opaque on purpose: it is part of the sticky head, and a transparent row
 *  there lets the rows scrolling underneath show through it. */
export const TABLE_FILTER_ROW = "bg-card hover:bg-card";
export const TABLE_HEAD = "border-r text-xs font-semibold last:border-r-0";
export const TABLE_ROW = "even:bg-muted/40";
export const TABLE_CELL = "border-r last:border-r-0";
/** a row pinned to the bottom of the scroll box — the line where a new entry is typed */
export const TABLE_FOOT = "sticky bottom-0 z-10 border-t bg-card";
