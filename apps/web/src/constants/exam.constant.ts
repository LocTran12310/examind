import type { QuestionType } from "@/interfaces/question.interface";

/** The parts of an exam (the official layout: I multiple choice, II true/false, III short answer, IV essay). */
export const SECTION_LABEL: Record<string, string> = { I: "Phần I", II: "Phần II", III: "Phần III", IV: "Phần IV" };

export const SECTION_OPTIONS = Object.entries(SECTION_LABEL).map(([value, label]) => ({ value, label }));

/** Which part a question type belongs to — the API derives a question's section the same way. */
export const SECTION_OF_TYPE: Record<QuestionType, string> = { mcq: "I", true_false: "II", short_answer: "III", essay: "IV" };

export const SECTION_ORDER = ["I", "II", "III", "IV"];
