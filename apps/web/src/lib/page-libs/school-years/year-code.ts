/** The year after `code` ("2026-2027" → "2027-2028"); this calendar year's when there is none yet. */
export function nextYearCode(code?: string): string {
  const y = code ? Number(code.slice(5)) : new Date().getFullYear();
  return `${y}-${y + 1}`;
}
