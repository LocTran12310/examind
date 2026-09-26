import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { weakestSubject } from "@/lib/page-libs/my-stats/weakest-subject";
import MyStatsPage from "@/app/(app)/me/stats/page";
import { MeProvider } from "@/hooks/common/use-me";
import { PracticeHistory } from "@/components/page-components/MyStats/PracticeHistory/PracticeHistory";
import { lastQuery, mockFetch, renderWithQuery as render, route, me } from "./helpers";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

afterEach(() => vi.unstubAllGlobals());

describe("my stats", () => {
  it("lists weakest leaf topics first", async () => {
    mockFetch(
      route("GET", /\/api\/stats\/topics\?/, [
        { id: "a", parent_id: null, name: "Đại số", path: "a", depth: 1, level_kind: "strand", points: 1, max_points: 2, answered: 8, ratio: 0.5 },
        { id: "b", parent_id: "a", name: "Mệnh đề", path: "a.b", depth: 2, level_kind: "topic", points: 0.25, max_points: 1, answered: 4, ratio: 0.25 },
        { id: "c", parent_id: "a", name: "Tập hợp", path: "a.c", depth: 2, level_kind: "topic", points: 0.75, max_points: 1, answered: 4, ratio: 0.75 },
      ]),
      route("GET", /\/api\/stats\/groups\?by=type/, [{ key: "mcq", label: "mcq", points: 1, max_points: 2, answered: 8, ratio: 0.5 }]),
      route("GET", "/api/me/practice", []),
      route("GET", "/api/me/mastery", [
        { topic_id: "a", parent_id: null, name: "Đại số", path: "a", depth: 1, mastery: 0.5, answers: 12, tracked: false, enough_data: true, weak: false },
        { topic_id: "b", parent_id: "a", name: "Mệnh đề", path: "a.b", depth: 2, mastery: 0.3, answers: 6, tracked: true, enough_data: true, weak: true },
        { topic_id: "c", parent_id: "a", name: "Tập hợp", path: "a.c", depth: 2, mastery: 0.7, answers: 6, tracked: true, enough_data: true, weak: false },
      ]),
    );
    render(<MeProvider value={me("student")}>
        <MyStatsPage />
      </MeProvider>);
    const weak = await screen.findByTestId("mastery");
    expect(weak.textContent?.indexOf("Mệnh đề")).toBeLessThan(weak.textContent?.indexOf("Tập hợp") ?? 0);
    expect(weak).not.toHaveTextContent("Đại số");
    // the order carries the same information; calling a student's topic "cần ôn nhất" passes a verdict (AC-04, ADR-02)
    expect(screen.getByRole("heading", { name: "Mức nắm vững (thấp trước)" })).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent(/yếu nhất|cần ôn nhất/);
  });
});

describe("môn đang yếu nhất", () => {
  const row = (subject: string | null, points: number, max: number, answered = 4) =>
    ({ id: subject ?? "x", parent_id: null, name: "n", path: "p", depth: 1, level_kind: "strand", subject_id: subject, points, max_points: max, answered, ratio: max ? points / max : null });

  it("là môn có tỉ lệ thấp nhất, không phải môn đầu bảng", () => {
    expect(weakestSubject([row("s1", 8, 10), row("s2", 2, 10)])).toBe("s2");
  });

  it("một môn chưa ai trả lời câu nào thì không phải môn yếu nhất — chưa đo khác với yếu", () => {
    // cùng một luật mà các dải mức nắm vững được dựng trên: 0 lượt là "chưa đủ dữ liệu", không phải 0%
    expect(weakestSubject([row("s1", 8, 10), row("s2", 0, 0, 0)])).toBe("s1");
  });

  it("chưa có gì để nói thì trả về null, chứ không đoán bừa một môn", () => {
    expect(weakestSubject([])).toBeNull();
    expect(weakestSubject([row(null, 5, 10)])).toBeNull(); // hàng "Chưa phân loại" không thuộc môn nào
  });
});

describe("một trang, một môn", () => {
  const topic = (id: string, subject: string, ratio: number) =>
    ({ id, parent_id: null, name: `Mạch ${id}`, path: id, depth: 1, level_kind: "strand", subject_id: subject, points: ratio, max_points: 1, answered: 4, ratio });
  const mastery = (id: string, subject: string | null) =>
    ({ topic_id: id, parent_id: null, name: `Chuyên đề ${id}`, path: id, depth: 1, subject_id: subject, mastery: 0.4, answers: 6, tracked: true, enough_data: true, weak: true });
  const run = (id: string, subject: string | null) =>
    ({ attempt_id: id, title: "Đề ôn", status: "submitted", started_at: "2026-09-22T00:00:00Z", submitted_at: "2026-09-22T00:30:00Z", score10: 6, subject_id: subject, note: null, groups: [] });

  const page = (...extra: Parameters<typeof mockFetch>) => {
    const f = mockFetch(
      route("GET", "/api/taxonomy", { subjects: [{ id: "s1", code: "toan", name: "Toán" }, { id: "s2", code: "ly", name: "Vật lý" }], grades: [], semesters: [] }),
      route("GET", /\/api\/stats\/topics\?/, [topic("a", "s1", 0.5), topic("b", "s2", 0.2)]),
      route("GET", /\/api\/stats\/groups\?by=type/, []),
      route("GET", "/api/me/mastery", [mastery("m1", "s1"), mastery("m2", "s2")]),
      route("GET", "/api/me/practice", [run("r1", "s1"), run("r2", "s2"), run("r3", null)]),
      ...extra,
    );
    render(<MeProvider value={me("student")}><MyStatsPage /></MeProvider>);
    return f;
  };

  it("mặc định là Mọi môn, và cả bốn khối đều đủ mọi môn", async () => {
    page();
    expect(await screen.findByRole("combobox", { name: "Môn" })).toHaveTextContent("Mọi môn");
    expect(await screen.findByText("Chuyên đề m1")).toBeInTheDocument();
    expect(screen.getByText("Chuyên đề m2")).toBeInTheDocument();
    expect(within(screen.getByTestId("practice-history")).getAllByRole("listitem")).toHaveLength(3);
  });

  it("chọn một môn thì mọi khối theo môn ấy, và lượt ôn không rõ môn không bị nhận bừa (AC-05, AC-07)", async () => {
    const u = userEvent.setup();
    const f = page();
    await u.click(await screen.findByRole("combobox", { name: "Môn" }));
    await u.click(await screen.findByRole("option", { name: "Toán" }));
    // mức nắm vững của môn khác biến mất, và lượt ôn cũ không có môn cũng không được gán vào Toán
    await waitFor(() => expect(screen.queryByText("Chuyên đề m2")).not.toBeInTheDocument());
    expect(screen.getByText("Chuyên đề m1")).toBeInTheDocument();
    expect(within(screen.getByTestId("practice-history")).getAllByRole("listitem")).toHaveLength(1);
    // và các con số theo chuyên đề được hỏi lại với đúng môn ấy
    await waitFor(() => expect(lastQuery(f, "/stats/topics").get("subject_id")).toBe("s1"));
  });
});

describe("lịch sử ôn tập gập lại được", () => {
  it("mặc định chỉ hiện vài lượt, nói còn bao nhiêu, và mở ra được (AC-06)", async () => {
    const items = Array.from({ length: 5 }, (_, i) => ({
      attempt_id: `a${i}`, title: "Đề ôn", status: "submitted" as const, started_at: "2026-09-22T00:00:00Z",
      submitted_at: "2026-09-22T00:30:00Z", score10: 6, subject_id: null, note: null, groups: [],
    }));
    const u = userEvent.setup();
    render(<PracticeHistory items={items} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
    expect(screen.getByText("Còn 2 lượt nữa.")).toBeInTheDocument();
    await u.click(screen.getByRole("button", { name: "Xem cả 5 lượt" }));
    expect(screen.getAllByRole("listitem")).toHaveLength(5);
    await u.click(screen.getByRole("button", { name: "Thu gọn" }));
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
  });
});
