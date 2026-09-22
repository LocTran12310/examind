/** The parts of an exam (the official layout: I multiple choice, II true/false, III short answer, IV essay). */
export const SECTION_LABEL: Record<string, string> = { I: "Phần I", II: "Phần II", III: "Phần III", IV: "Phần IV" };

export const SECTION_OPTIONS = Object.entries(SECTION_LABEL).map(([value, label]) => ({ value, label }));
