import type { RolloverAction, YearStatus } from "@/interfaces/school-year.interface";

export const YEAR_STATUS_LABEL: Record<YearStatus, string> = { planning: "Chuẩn bị", active: "Đang học", closed: "Đã khóa" };

export const YEAR_STATUS_OPTIONS = Object.entries(YEAR_STATUS_LABEL).map(([value, label]) => ({ value, label }));

export const ROLLOVER_ACTION_LABEL: Record<RolloverAction, string> = { promote: "Lên lớp", retain: "Ở lại lớp", transfer: "Chuyển đi", graduate: "Tốt nghiệp" };
