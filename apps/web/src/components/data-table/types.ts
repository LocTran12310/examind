import type { RowData } from "@tanstack/react-table";

export type FilterSpec =
  | { kind: "text"; key?: string; placeholder?: string }
  | { kind: "select"; key?: string; options: { value: string; label: string }[] }
  | { kind: "date"; key?: string }
  | { kind: "number"; key?: string };

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
