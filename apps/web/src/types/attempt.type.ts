export type AttemptStatus = "in_progress" | "submitted";

/** One answer as sent and stored: `{key}` (mcq), `{a: true, …}` (true/false), `{value}` (short answer), `{text}` (essay). */
export type AnswerResponse = Record<string, unknown> | null;
