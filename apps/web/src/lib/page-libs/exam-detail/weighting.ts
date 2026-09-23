import { SECTION_OF_TYPE, SECTION_ORDER } from "@/constants/exam.constant";
import type { Exam, ExamQuestion } from "@/interfaces/exam.interface";
import type { QuestionType } from "@/interfaces/question.interface";

/** Points are stored as floats; the API rounds the same way before it shows a score. */
const round2 = (n: number) => Math.round(n * 100) / 100;

/** A number as Vietnamese copy writes it: 0,25 · 2,5 · 10. */
export function formatPoints(n: number): string {
  return String(round2(n)).replace(".", ",");
}

/** A question whose points were edited away from the default of its type. */
export interface OddQuestion {
  id: string;
  position: number;
  points: number;
  /** the default of its type, i.e. what it would be worth untouched */
  expected: number;
}

export interface WeightingSection {
  section: string;
  types: QuestionType[];
  count: number;
  /** what every question of the part carries, or null when they do not agree */
  perQuestion: number | null;
  /** the per-type default in force for the part */
  defaultPoints: number;
  total: number;
  odd: OddQuestion[];
}

export interface Weighting {
  sections: WeightingSection[];
  count: number;
  /** the points of the paper as written */
  raw: number;
  scaleTo: number;
  /** what one raw point becomes on the scale; null when there is nothing to convert */
  factor: number | null;
  /** the raw total already is the scale — a conversion would only confuse */
  exact: boolean;
  odd: OddQuestion[];
}

const sectionOf = (q: ExamQuestion) => q.section || SECTION_OF_TYPE[q.type];
const rank = (s: string) => (SECTION_ORDER.indexOf(s) < 0 ? SECTION_ORDER.length : SECTION_ORDER.indexOf(s));

/** What each part of the exam is worth, what the paper is worth, and what that becomes on `scale_to`
 *  (review-ux AC-06). Derived from the exam payload — the model itself does not change (A-04). */
export function examWeighting(exam: Pick<Exam, "questions" | "settings">): Weighting {
  const defaults = exam.settings.points_by_type;
  const scaleTo = round2(exam.settings.scale_to);
  const present = [...new Set(exam.questions.map(sectionOf))].sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
  const sections = present.map<WeightingSection>((section) => {
    const qs = exam.questions.filter((q) => sectionOf(q) === section);
    const types = [...new Set(qs.map((q) => q.type))];
    const values = new Set(qs.map((q) => round2(q.points)));
    return {
      section,
      types,
      count: qs.length,
      perQuestion: values.size === 1 ? [...values][0] : null,
      defaultPoints: round2(defaults[types[0]] ?? 0),
      total: round2(qs.reduce((s, q) => s + q.points, 0)),
      odd: qs
        .filter((q) => round2(q.points) !== round2(defaults[q.type] ?? q.points))
        .map((q) => ({ id: q.id, position: q.position, points: round2(q.points), expected: round2(defaults[q.type]) })),
    };
  });
  const raw = round2(exam.questions.reduce((s, q) => s + q.points, 0));
  return { sections, count: exam.questions.length, raw, scaleTo, factor: raw ? round2(scaleTo / raw) : null, exact: raw === scaleTo, odd: sections.flatMap((s) => s.odd) };
}
