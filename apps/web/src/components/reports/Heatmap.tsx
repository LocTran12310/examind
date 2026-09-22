"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export interface HeatmapData {
  columns: { id: string; name: string; path: string }[];
  rows: { student_id: string; full_name: string; username: string; cells: Record<string, { ratio: number | null; answered: number }> }[];
}

export function heatColor(r: number | null | undefined): string {
  if (r === null || r === undefined) return "var(--muted)";
  const hue = Math.round(r * 120); // 0 red → 120 green
  return `hsl(${hue} 70% ${85 - r * 20}%)`;
}

export function Heatmap({ data }: { data: HeatmapData }) {
  if (!data.rows.length) return <p className="text-sm text-muted-foreground">Lớp chưa có học sinh.</p>;
  return (
    <Table className="w-auto border-separate border-spacing-1 text-xs" data-testid="heatmap">
      <TableHeader>
        <TableRow className="border-0 hover:bg-transparent">
          <TableHead />
          {data.columns.map((c) => (
            <TableHead key={c.id} className="h-auto max-w-28 truncate px-1 text-muted-foreground" title={c.name}>
              {c.name}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.rows.map((r) => (
          <TableRow key={r.student_id} className="border-0 hover:bg-transparent">
            <TableCell className="p-0 pr-2 text-sm">{r.full_name}</TableCell>
            {data.columns.map((c) => {
              const cell = r.cells[c.id];
              return (
                <TableCell key={c.id} className="h-8 min-w-14 rounded p-0 text-center text-neutral-900 tabular-nums" style={{ background: heatColor(cell?.ratio) }} title={cell ? `${cell.answered} lượt` : "chưa làm"}>
                  {cell?.ratio === null || cell?.ratio === undefined ? "" : `${Math.round(cell.ratio * 100)}%`}
                </TableCell>
              );
            })}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
