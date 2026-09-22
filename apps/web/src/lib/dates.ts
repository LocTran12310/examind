/** Older helpers, now on the business time zone (see ./datetime). */
import { formatDateTime, fromBusinessInput, toBusinessInput } from "./datetime";

/** `datetime-local` value in business time (Asia/Ho_Chi_Minh), minutes precision. */
export function toLocalInput(d: Date): string {
  return toBusinessInput(d);
}

/** `datetime-local` value (business time) → ISO UTC. */
export function fromLocalInput(v: string): string {
  return fromBusinessInput(v);
}

export function fmt(iso: string | null | undefined): string {
  return formatDateTime(iso);
}
