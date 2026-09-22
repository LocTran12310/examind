import { describe, expect, it } from "vitest";
import { businessToday, formatDate, formatDateTime, formatTime, fromBusinessInput, toBusinessInput } from "./datetime";

describe("datetime (business zone Asia/Ho_Chi_Minh, whatever the browser)", () => {
  it("formats UTC instants in +07:00", () => {
    expect(formatDateTime("2026-01-01T00:00:00Z")).toBe("01/01/2026 07:00");
    expect(formatDateTime("2026-09-22T17:30:05Z", { withSeconds: true })).toBe("23/09/2026 00:30:05"); // past midnight in Hà Nội
    expect(formatDate("2026-09-21T18:00:00Z")).toBe("22/09/2026");
    expect(formatDate("2026-09-22")).toBe("22/09/2026"); // a calendar day stays that day
    expect(formatTime("2026-09-22T10:44:00Z")).toBe("17:44");
    expect(formatDateTime(null)).toBe("—");
    expect(formatDateTime("nope")).toBe("—");
  });

  it("datetime-local inputs round-trip with an explicit offset", () => {
    expect(toBusinessInput("2026-09-22T10:44:00Z")).toBe("2026-09-22T17:44");
    expect(fromBusinessInput("2026-09-22T17:44")).toBe("2026-09-22T10:44:00.000Z");
    expect(fromBusinessInput(toBusinessInput("2026-03-01T23:59:00Z"))).toBe("2026-03-01T23:59:00.000Z");
    expect(businessToday("2026-09-21T17:00:00Z")).toBe("2026-09-22");
  });
});
