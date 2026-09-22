/** When a student sees answers and solutions of a submitted attempt. */
export type ResultsPolicy = "after_submit" | "after_close" | "never";

/** Where a student stands with one assignment (`GET /me/assignments`). */
export type AssignmentState = "open" | "upcoming" | "closed";
