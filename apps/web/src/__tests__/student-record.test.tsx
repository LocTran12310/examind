import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MeProvider } from "@/app/(app)/AppShell";
import { StudentRecord } from "@/components/students/StudentRecord";
import { me, mockFetch, route } from "./helpers";

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
        <StudentRecord id="s1" />
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
