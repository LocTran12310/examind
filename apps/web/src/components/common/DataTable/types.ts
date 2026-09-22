import type { RowData } from "@tanstack/react-table";

/** `param: true` = the value is a parameter of the resource (sent at the top of the search body),
 *  not a column filter — e.g. the subject of the Tags page, which also accepts "shared". */
export type FilterSpec =
  | { kind: "text"; key?: string; placeholder?: string; param?: boolean }
  | { kind: "select"; key?: string; options: { value: string; label: string }[]; param?: boolean }
  | { kind: "date"; key?: string; param?: boolean }
  | { kind: "number"; key?: string; param?: boolean };

declare module "@tanstack/react-table" {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData extends RowData, TValue> {
    /** Filter shown in the row under the header; `key` defaults to the column id (= API param). */
    filter?: FilterSpec;
    /** Sort key sent to the API (`sort=key` / `sort=-key`); omit to make the column unsortable. */
    sort?: string;
    align?: "right" | "center";
    className?: string;
  }
}
