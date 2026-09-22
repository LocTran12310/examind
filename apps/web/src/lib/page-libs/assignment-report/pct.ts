/** A ratio as a whole percentage, "—" when nobody answered. */
export function pct(r: number | null | undefined): string {
  return r === null || r === undefined ? "—" : `${Math.round(r * 100)}%`;
}
