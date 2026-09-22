import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MeProvider } from "@/app/(app)/AppShell";
import StructurePage from "@/app/(app)/org/structure/page";
import { ThemeProvider } from "@/components/app/ThemeProvider";
import type { Structure } from "@/lib/types";
import { lastQuery, me, mockFetch, page, route } from "./helpers";
import { searchOf, setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const structure: Structure = {
  levels: [
    { id: "thcs", code: "thcs", name: "Trung học cơ sở", grade_from: 6, grade_to: 9, class_count: 0, student_count: 0, grades: [{ id: "g6", level: 6, name: "Lớp 6", class_count: 0, student_count: 0, classes: [] }] },
    {
      id: "thpt", code: "thpt", name: "Trung học phổ thông", grade_from: 10, grade_to: 12, class_count: 2, student_count: 15,
      grades: [{ id: "g10", level: 10, name: "Lớp 10", class_count: 2, student_count: 15, classes: [{ id: "c1", name: "10A1", school_year: "2026-2027", member_count: 15 }, { id: "c2", name: "10A2", school_year: "2026-2027", member_count: 0 }] }],
    },
  ],
  unassigned: [],
};

function serve() {
  return mockFetch(
    route("GET", "/api/structure", structure),
    route("GET", /^\/api\/school-levels\?/, page([{ id: "thpt", code: "thpt", name: "Trung học phổ thông", grade_from: 10, grade_to: 12, sort: 1, grade_count: 3 }])),
    route("GET", /^\/api\/grades\?/, page([{ id: "g10", level: 10, name: "Lớp 10", school_level_id: "thpt", class_count: 2 }])),
    route("GET", /^\/api\/classes\?/, page([{ id: "c1", name: "10A1", grade: 10, grade_id: "g10", school_year: "2026-2027", member_count: 15, created_at: "" }])),
    route("GET", /^\/api\/users\?/, page([{ id: "s1", username: "buivanchau", full_name: "Bùi Văn Châu", role: "student", class_ids: ["c1"] }])),
    route("DELETE", "/api/grades/g10", { code: "in_use", message: "Khối còn 2 lớp" }, 409),
  );
}

const renderPage = () =>
  render(
    <ThemeProvider>
      <MeProvider value={me("org_admin")}>
        <StructurePage />
      </MeProvider>
    </ThemeProvider>,
  );

beforeEach(() => setUrl("/org/structure"));

describe("school structure", () => {
  it("shows the tree with class and student counts", async () => {
    serve();
    renderPage();
    const tree = await screen.findByRole("navigation", { name: "Cơ cấu trường" });
    const thpt = within(tree).getByRole("group", { name: "Trung học phổ thông" });
    expect(thpt).toHaveTextContent("(10–12)");
    expect(thpt).toHaveTextContent("2 lớp");
    expect(thpt).toHaveTextContent("15");
    expect(within(thpt).getByText("10A1")).toBeInTheDocument();
  });

  it("level → its grades, grade → its classes, class → its students, all server-side with the node in the URL", async () => {
    const fetch = serve();
    const u = userEvent.setup();
    renderPage();
    const tree = await screen.findByRole("navigation", { name: "Cơ cấu trường" });
    await u.click(within(tree).getByRole("button", { name: /Trung học phổ thông/ }));
    await waitFor(() => expect(lastQuery(fetch, "/grades").get("school_level_id")).toBe("thpt"));
    expect(searchOf().get("node")).toBe("level:thpt");
    await u.click(within(tree).getByRole("button", { name: /^Lớp 10/ }));
    await waitFor(() => expect(lastQuery(fetch, "/classes").get("grade_id")).toBe("g10"));
    await u.click(within(tree).getByRole("button", { name: /10A1/ }));
    expect(await screen.findByText("Bùi Văn Châu")).toBeInTheDocument();
    expect(lastQuery(fetch, "/users").get("class_id")).toBe("c1");
    expect(screen.getByText("Lớp 10A1")).toBeInTheDocument();
    expect(screen.getByText("Trung học phổ thông › Lớp 10")).toBeInTheDocument();
  });

  it("deleting a grade that still has classes shows the server's reason", async () => {
    setUrl("/org/structure?node=level:thpt");
    serve();
    const u = userEvent.setup();
    renderPage();
    const row = await screen.findByRole("row", { name: /Lớp 10/ });
    await u.click(within(row).getByRole("checkbox"));
    await u.click(screen.getByRole("button", { name: "Xóa" }));
    await u.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xóa" }));
    expect(await screen.findByText("Khối còn 2 lớp")).toBeInTheDocument();
  });
});
