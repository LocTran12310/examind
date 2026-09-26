import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RolloverPage } from "@/components/page-components/Rollover/RolloverPage";
import { mockFetch, renderWithQuery as render, route } from "./helpers";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const st = (id: string, name: string, action: string) => ({ user_id: id, full_name: name, username: id, current_status: "active", action });
const plan = {
  source_year: { id: "y1", code: "2026-2027", status: "active" },
  target_code: "2027-2028",
  target_year_id: null,
  top_grade: 12,
  classes: [
    { source_class_id: "c10", source_name: "10A1", grade: 10, graduating: false, target_name: "11A1", target_grade: 11, target_exists: false, students: [st("an", "An", "promote"), st("binh", "Bình", "promote")] },
    { source_class_id: "c12", source_name: "12C", grade: 12, graduating: true, target_name: null, target_grade: null, target_exists: false, students: [st("em", "Em", "graduate")] },
  ],
};

describe("rollover wizard", () => {
  it("proposes the mapping, lets me change exceptions and commits them", async () => {
    const fetch = mockFetch(
      route("POST", "/api/school-years/y1/rollover/preview", plan),
      route("POST", "/api/school-years/y1/rollover/commit", { target_year_id: "y2", target_code: "2027-2028", classes_created: ["11A1", "10A1"], promote: 1, retain: 1, transfer: 0, graduate: 1 }),
    );
    const u = userEvent.setup();
    render(<RolloverPage yearId="y1" />);
    const c10 = await screen.findByTestId("plan-10A1");
    expect(within(c10).getByRole("textbox", { name: "Lớp mới của 10A1" })).toHaveValue("11A1");
    expect(screen.getByTestId("plan-12C")).toHaveTextContent("Tốt nghiệp");
    expect(screen.getByLabelText("Tổng hợp")).toHaveTextContent("Lên lớp: 2");
    await u.click(within(c10).getByRole("button", { name: /Lớp 10A1/ }));
    await u.click(await within(c10).findByRole("combobox", { name: "Năm mới của Bình" }));
    await u.click(await screen.findByRole("option", { name: "Ở lại lớp (10A1)" }));
    expect(within(c10).getByRole("combobox", { name: "Năm mới của Bình" })).toHaveTextContent("Ở lại lớp (10A1)");
    expect(screen.getByLabelText("Tổng hợp")).toHaveTextContent("Ở lại lớp: 1");
    await u.click(screen.getByRole("button", { name: "Xác nhận chuyển năm" }));
    const dlg = await screen.findByRole("alertdialog");
    expect(dlg).toHaveTextContent("1 lên lớp, 1 ở lại, 0 chuyển đi, 1 tốt nghiệp");
    await u.click(within(dlg).getByRole("button", { name: "Chuyển năm" }));
    expect(await screen.findByText(/Đã chuyển sang 2027-2028/)).toHaveTextContent("Tạo lớp: 11A1, 10A1");
    const body = JSON.parse(String((fetch.mock.calls.find(([url]) => url === "/api/school-years/y1/rollover/commit")?.[1] as RequestInit).body));
    expect(body.activate_target).toBe(true);
    expect(body.classes[0].students).toEqual([{ user_id: "an", action: "promote" }, { user_id: "binh", action: "retain" }]);
    await waitFor(() => expect(fetch).toHaveBeenCalled());
  });

  it("keeps every class folded: the header carries the plan, the students are one click away", async () => {
    mockFetch(route("POST", "/api/school-years/y1/rollover/preview", plan));
    const u = userEvent.setup();
    render(<RolloverPage yearId="y1" />);
    const c10 = await screen.findByTestId("plan-10A1");
    // folded, the header still answers "how many" and "what happens to them", and stays editable
    expect(c10).toHaveTextContent("2 học sinh");
    expect(screen.getByTestId("summary-10A1")).toHaveTextContent("Lên lớp 2");
    expect(within(c10).getByRole("textbox", { name: "Lớp mới của 10A1" })).toHaveValue("11A1");
    expect(within(c10).getByRole("button", { name: "Tất cả: Lên lớp" })).toBeInTheDocument();
    expect(screen.queryByText("An")).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Năm mới của An" })).not.toBeInTheDocument();
    await u.click(within(c10).getByRole("button", { name: /Lớp 10A1/ }));
    expect(await within(c10).findByText("An")).toBeInTheDocument();
    expect(within(c10).getByRole("combobox", { name: "Năm mới của Bình" })).toBeInTheDocument();
    expect(screen.queryByText("Em")).not.toBeInTheDocument();
    await u.click(within(c10).getByRole("combobox", { name: "Năm mới của Bình" }));
    await u.click(await screen.findByRole("option", { name: "Ở lại lớp (10A1)" }));
    expect(screen.getByTestId("summary-10A1")).toHaveTextContent("Lên lớp 1 · Ở lại lớp 1");
    expect(screen.getByLabelText("Tổng hợp")).toHaveTextContent("Lên lớp: 1");
    expect(screen.getByLabelText("Tổng hợp")).toHaveTextContent("Ở lại lớp: 1");
    await u.click(within(c10).getByRole("button", { name: /Lớp 10A1/ }));
    await waitFor(() => expect(screen.queryByText("An")).not.toBeInTheDocument());
    expect(screen.getByTestId("summary-10A1")).toHaveTextContent("Lên lớp 1 · Ở lại lớp 1");
  });

  it("folds each class on its own: opening one leaves the others closed", async () => {
    mockFetch(route("POST", "/api/school-years/y1/rollover/preview", plan));
    const u = userEvent.setup();
    render(<RolloverPage yearId="y1" />);
    const c12 = await screen.findByTestId("plan-12C");
    expect(c12).toHaveTextContent("1 học sinh");
    expect(screen.getByTestId("summary-12C")).toHaveTextContent("Tốt nghiệp 1");
    await u.click(within(c12).getByRole("button", { name: /Lớp 12C/ }));
    expect(await within(c12).findByText("Em")).toBeInTheDocument();
    expect(screen.queryByText("An")).not.toBeInTheDocument();
  });
});
