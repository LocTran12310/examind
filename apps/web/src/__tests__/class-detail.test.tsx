import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ClassDetailPage } from "@/components/page-components/ClassDetail/ClassDetailPage";
import type { ClassSummary } from "@/interfaces/mastery.interface";
import { mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const klass = { id: "c1", name: "12A1", grade: 12, grade_id: "g12", school_year: "2026-2027", school_year_id: "y1", member_count: 25, created_at: "" };

const summary = (o: Partial<ClassSummary> = {}): ClassSummary => ({
  assignments: 6,
  sittings: 150,
  average: 6.09,
  distribution: [0, 0, 1, 3, 12, 30, 40, 38, 20, 6],
  weakest: [
    { name: "Dãy số, cấp số cộng", ratio: 0.31, answered: 48 },
    { name: "Thể tích khối chóp", ratio: 0.46, answered: 52 },
  ],
  ...o,
});

const mount = (s: ClassSummary) =>
  mockFetch(
    route("GET", "/api/classes/c1", klass),
    route("GET", "/api/classes/c1/summary", s),
    route("GET", "/api/classes/c1/overview", []),
    route("POST", "/api/users/search", searchPage([])),
  );

describe("trang lớp: tổng quan cả lớp và từng học sinh", () => {
  it("mở ra ở Tổng quan, với số của cả lớp", async () => {
    // AC-03. Người dạy hỏi "lớp thế nào" trước khi hỏi "em nào", nên tab ấy là tab mặc định.
    mount(summary());
    render(<ClassDetailPage id="c1" />);

    expect(await screen.findByTestId("cs-assignments")).toHaveTextContent("6");
    expect(screen.getByTestId("cs-average")).toHaveTextContent("6.09");
    expect(screen.getByTestId("cs-distribution").children).toHaveLength(10);
    expect(screen.getByTestId("cs-weakest")).toHaveTextContent("Dãy số, cấp số cộng 31%");
  });

  it("chuyển sang Học sinh thì thấy danh sách, không còn số của lớp", async () => {
    mount(summary());
    render(<ClassDetailPage id="c1" />);
    await screen.findByTestId("cs-average");

    await userEvent.click(screen.getByRole("tab", { name: "Học sinh" }));
    await waitFor(() => expect(screen.queryByTestId("cs-average")).not.toBeInTheDocument());
  });

  it("lớp chưa ai nộp nói rõ, thay vì trưng một hàng số 0", async () => {
    // AC-04. `average: null` là "chưa đo"; 0 là "đo rồi và bằng không". Hai điều khác nhau, và một bảng toàn 0
    // trông y như lớp làm bài mà không ai được điểm nào.
    mount(summary({ sittings: 0, average: null, distribution: Array(10).fill(0), weakest: [] }));
    render(<ClassDetailPage id="c1" />);

    expect(await screen.findByText(/Chưa có bài nộp nào/)).toBeInTheDocument();
    expect(screen.queryByTestId("cs-average")).not.toBeInTheDocument();
    expect(screen.queryByTestId("cs-distribution")).not.toBeInTheDocument();
  });
});

describe("phổ điểm: rê chuột vào một cột", () => {
  it("nói khoảng điểm, bao nhiêu bài, và chiếm bao nhiêu phần", async () => {
    mount(summary());
    render(<ClassDetailPage id="c1" />);
    await screen.findByTestId("cs-distribution");

    await userEvent.hover(screen.getByTestId("bucket-6"));
    const tip = await screen.findByRole("tooltip");
    expect(tip).toHaveTextContent("6–7 điểm");
    expect(tip).toHaveTextContent("40 bài");
    expect(tip).toHaveTextContent("27% của 150 bài đã nộp");
  });

  it("một khoảng không ai đạt vẫn rê được, và nói là không có bài nào", async () => {
    // Bản đầu đặt tooltip lên chính cái thanh, mà chiều cao thanh tỉ lệ với số bài — nên cột 0 lượt cao 0 và
    // không cách nào rê vào. Đúng những khoảng trống ấy mới là thứ người dạy muốn hỏi: "không em nào được 0–1 à?"
    mount(summary());
    render(<ClassDetailPage id="c1" />);
    await screen.findByTestId("cs-distribution");

    await userEvent.hover(screen.getByTestId("bucket-0"));
    expect(await screen.findByRole("tooltip")).toHaveTextContent("Không có bài nào");
  });
});
