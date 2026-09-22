/** The school year of a date on the client: a new year starts in August. */
export function currentSchoolYear(d = new Date()): string {
  const start = d.getMonth() >= 7 ? d.getFullYear() : d.getFullYear() - 1;
  return `${start}-${start + 1}`;
}
