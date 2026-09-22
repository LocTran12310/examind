import { describe, expect, it } from "vitest";
import { toSearchBody } from "./search-body";

describe("toSearchBody", () => {
  it("turns the URL table state into the search body", () => {
    const p = new URLSearchParams("q=%20bien%20&sort=name,-created_at&page=3&page_size=50&name=ph&name_op=%2B&group=method&created_at_from=2026-09-01&created_at_to=2026-09-30&grade=10&grade_op=%3E%3D&ignored=x");
    expect(toSearchBody(p, { name: "text", group: "select", created_at: "date", grade: "number" }, { subject_id: "s1", empty: "" })).toEqual({
      page: 3,
      limit: 50,
      q: "bien",
      sort: [{ field: "name" }, { field: "created_at", desc: true }],
      filters: {
        name: { value: "ph", operator: "+" },
        group: { value: "method" },
        created_at: { from: "2026-09-01", to: "2026-09-30" },
        grade: { value: 10, operator: ">=" },
      },
      subject_id: "s1",
    });
  });

  it("resource parameters go to the top of the body", () => {
    expect(toSearchBody(new URLSearchParams("subject_id=shared"), { subject_id: "param" }, { include_shared: false })).toEqual({
      page: 1,
      limit: 20,
      subject_id: "shared",
      include_shared: false,
    });
  });

  it("defaults and 'all'", () => {
    expect(toSearchBody(new URLSearchParams(""), {})).toEqual({ page: 1, limit: 20 });
    expect(toSearchBody(new URLSearchParams("page_size=all&day=2026-09-22&day_op=%3C"), { day: "date" })).toEqual({
      page: 1,
      limit: 1000,
      filters: { day: { value: "2026-09-22", operator: "<" } },
    });
  });
});
