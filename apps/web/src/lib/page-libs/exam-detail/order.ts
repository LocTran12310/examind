/** Swap two ids in a list (the "Đổi chỗ với câu …" choice). */
export function swapped(ids: string[], a: string, b: string): string[] {
  const i = ids.indexOf(a),
    j = ids.indexOf(b);
  if (i < 0 || j < 0) return ids;
  const out = [...ids];
  [out[i], out[j]] = [out[j], out[i]];
  return out;
}

/** Move `id` to where `before` is (drag and drop). */
export function movedTo(ids: string[], id: string, before: string): string[] {
  if (id === before) return ids;
  const out = ids.filter((x) => x !== id);
  out.splice(out.indexOf(before) + (ids.indexOf(id) < ids.indexOf(before) ? 1 : 0), 0, id);
  return out;
}
