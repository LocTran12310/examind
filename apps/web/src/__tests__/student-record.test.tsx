import { screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MeProvider } from "@/hooks/common/use-me";
import { StudentRecordPage } from "@/components/page-components/StudentRecord/StudentRecordPage";
import { me, mockFetch, renderWithQuery as render, route } from "./helpers";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

describe("student record", () => {
  it("shows one card per year with classes, status and results per term and topic", async () => {
    mockFetch(
      route("GET", "/api/students/s1/record", {
        student: { id: "s1", username: "lan", full_name: "Lan" },
        years: [
          { year: { id: "y2", code: "2027-2028", status: "active" }, classes: [{ id: "k11", name: "11A1", grade: 11, status: "active", status_label: "Đang học" }], answered: 0, ratio: null, attempts: 0, terms: {}, topics: [] },
          {
            year: { id: "y1", code: "2026-2027", status: "closed" },
            classes: [{ id: "k10", name: "10A1", grade: 10, status: "promoted", status_label: "Lên lớp" }],
            answered: 40, ratio: 0.725, attempts: 3, terms: { hk1: { answered: 20, ratio: 0.6 }, hk2: { answered: 20, ratio: 0.85 } },
            topics: [{ id: "t1", name: "Đại số", answered: 30, ratio: 0.7 }],
          },
        ],
      }),
    );
    const { findAllByRole } = render(
      <MeProvider value={me("teacher")}>
        <StudentRecordPage id="s1" />
      </MeProvider>,
    );
    const cards = await findAllByRole("listitem");
    expect(cards[0]).toHaveTextContent("Năm học 2027-2028");
    expect(cards[0]).toHaveTextContent("Lớp 11A1");
    const y1 = cards[1];
    expect(y1).toHaveTextContent("Đã khóa");
    expect(within(y1).getByText("Lên lớp")).toBeInTheDocument();
    expect(y1).toHaveTextContent("73%");
    expect(y1).toHaveTextContent("Học kỳ 285%");
    expect(y1).toHaveTextContent("Đại số");
    expect(screen.queryByRole("button", { name: "Lịch sử" })).toBeNull(); // history is for org admins
  });
});

describe("lịch sử làm bài trên hồ sơ", () => {
  const record = { student: { id: "s1", username: "lan", full_name: "Lan" }, years: [] };
  const row = (o: Record<string, unknown> = {}) => ({
    attempt_id: "a1", exam_title: "Thi thử 12A1 lần 1", assignment_title: "Thi thử 12A1 lần 1",
    started_at: "2026-09-25T06:00:00+00:00", submitted_at: "2026-09-25T06:25:00+00:00",
    minutes: 25, score: 7.5, max_score: 10, score10: 7.5, status: "submitted", auto_submitted: false,
    student_id: "s1", student_name: "Lan", username: "lan", ...o,
  });

  it("nói em ấy làm đề nào, lúc nào, mất bao nhiêu phút", async () => {
    mockFetch(
      route("GET", "/api/students/s1/record", record),
      route("POST", "/api/attempts/search", { data: [row()], total: 1, page: 1, limit: 50 }),
    );
    render(<MeProvider value={me("teacher")}><StudentRecordPage id="s1" /></MeProvider>);

    const table = await screen.findByTestId("attempt-history");
    expect(within(table).getByText("Thi thử 12A1 lần 1")).toBeInTheDocument();
    expect(within(table).getByText("25 phút")).toBeInTheDocument();
    expect(within(table).getByText("7.5")).toBeInTheDocument();
  });

  it("lượt hệ thống tự đóng vẫn nằm đó, có dấu riêng", async () => {
    // AC-02. Giấu đi thì cột thời gian nói dối về đúng những lượt đáng chú ý nhất.
    mockFetch(
      route("GET", "/api/students/s1/record", record),
      route("POST", "/api/attempts/search", { data: [row({ auto_submitted: true })], total: 1, page: 1, limit: 50 }),
    );
    render(<MeProvider value={me("teacher")}><StudentRecordPage id="s1" /></MeProvider>);

    expect(await screen.findByText("tự nộp khi hết giờ")).toBeInTheDocument();
  });

  it("lượt đang làm dở chưa có thời gian, và không hiện 0", async () => {
    // `null` là chưa nộp; `0` là nộp gần như tức thì. Trưng 0 ở đây là khẳng định một điều chưa đo được.
    mockFetch(
      route("GET", "/api/students/s1/record", record),
      route("POST", "/api/attempts/search", { data: [row({ submitted_at: null, minutes: null, score: null, score10: null, status: "in_progress" })], total: 1, page: 1, limit: 50 }),
    );
    render(<MeProvider value={me("teacher")}><StudentRecordPage id="s1" /></MeProvider>);

    const table = await screen.findByTestId("attempt-history");
    expect(within(table).getByText("đang làm")).toBeInTheDocument();
    expect(within(table).queryByText("0 phút")).not.toBeInTheDocument();
  });

  it("em chưa làm bài nào thì nói rõ", async () => {
    mockFetch(
      route("GET", "/api/students/s1/record", record),
      route("POST", "/api/attempts/search", { data: [], total: 0, page: 1, limit: 50 }),
    );
    render(<MeProvider value={me("teacher")}><StudentRecordPage id="s1" /></MeProvider>);

    expect(await screen.findByText("Em này chưa làm bài nào.")).toBeInTheDocument();
  });
});
