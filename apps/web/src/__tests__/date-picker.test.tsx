import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import { DatePicker, DateTimePicker } from "@/components/app/DatePicker";

function Day({ initial = "" }: { initial?: string }) {
  const [v, setV] = useState(initial);
  return (
    <>
      <DatePicker aria-label="Ngày thi" value={v} onChange={setV} />
      <output>{v}</output>
    </>
  );
}

function Moment({ initial }: { initial: string }) {
  const [v, setV] = useState(initial);
  return (
    <>
      <DateTimePicker aria-label="Mở lúc" value={v} onChange={setV} />
      <output>{v}</output>
    </>
  );
}

describe("DatePicker (shadcn Popover + Calendar, no native date input)", () => {
  it("shows dd/MM/yyyy, picks a day as YYYY-MM-DD and clears", async () => {
    const u = userEvent.setup();
    const { container } = render(<Day initial="2026-09-22" />);
    expect(container.querySelector('input[type="date"]')).toBeNull();
    expect(screen.getByRole("button", { name: "Ngày thi" })).toHaveTextContent("22/09/2026");
    await u.click(screen.getByRole("button", { name: "Ngày thi" }));
    await u.click(within(await screen.findByRole("grid")).getByRole("button", { name: /\b15\b/ }));
    expect(screen.getByRole("status")).toHaveTextContent("2026-09-15");
    await u.click(screen.getByRole("button", { name: "Xóa Ngày thi" }));
    expect(screen.getByRole("status")).toHaveTextContent("");
  });

  it("DateTimePicker keeps the datetime-local contract: date from the calendar, HH:mm typed", async () => {
    const u = userEvent.setup();
    render(<Moment initial="2026-09-22T10:44" />);
    const time = screen.getByLabelText("Mở lúc — giờ");
    await u.clear(time);
    await u.type(time, "8:05{Enter}");
    expect(screen.getByRole("status")).toHaveTextContent("2026-09-22T08:05");
    await u.clear(time);
    await u.type(time, "25:00");
    await u.tab();
    expect(screen.getByRole("status")).toHaveTextContent("2026-09-22T08:05");
    expect(time).toHaveValue("08:05");
  });
});
