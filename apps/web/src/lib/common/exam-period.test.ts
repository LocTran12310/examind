import { describe, expect, it } from "vitest";
import { parsePeriod, periodLabel, periodOptions, periodValue } from "./exam-period";

describe("đợt kiểm tra", () => {
  it("labels term × kind the way teachers say it", () => {
    expect(periodLabel("hk1", "Giữa kỳ")).toBe("Giữa kỳ 1");
    expect(periodLabel("hk2", "Cuối kỳ")).toBe("Cuối kỳ 2");
    expect(periodLabel("hk2", "Thi thử")).toBe("Thi thử · HK2");
    expect(periodLabel(null, "Khảo sát")).toBe("Khảo sát");
    expect(periodLabel("hk1", null)).toBe("Học kỳ 1");
  });

  it("round-trips through the picker value and lists the periodic ones first", () => {
    expect(parsePeriod(periodValue("hk2", "Giữa kỳ"))).toEqual({ semester_code: "hk2", exam_kind: "Giữa kỳ" });
    expect(parsePeriod(periodValue(null, "Khác"))).toEqual({ semester_code: undefined, exam_kind: "Khác" });
    expect(periodOptions().slice(0, 4).map((o) => o.label)).toEqual(["Giữa kỳ 1", "Cuối kỳ 1", "Giữa kỳ 2", "Cuối kỳ 2"]);
    expect(periodOptions(true).some((o) => o.label === "Học kỳ 1 (mọi loại)")).toBe(true);
  });
});
