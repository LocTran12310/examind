"use client";

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
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-1 text-xs" data-testid="heatmap">
        <thead>
          <tr>
            <th />
            {data.columns.map((c) => (
              <th key={c.id} className="max-w-28 truncate px-1 font-medium text-muted-foreground" title={c.name}>
                {c.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((r) => (
            <tr key={r.student_id}>
              <td className="whitespace-nowrap pr-2 text-sm">{r.full_name}</td>
              {data.columns.map((c) => {
                const cell = r.cells[c.id];
                return (
                  <td key={c.id} className="h-8 min-w-14 rounded text-center text-neutral-900 tabular-nums" style={{ background: heatColor(cell?.ratio) }} title={cell ? `${cell.answered} lượt` : "chưa làm"}>
                    {cell?.ratio === null || cell?.ratio === undefined ? "" : `${Math.round(cell.ratio * 100)}%`}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
