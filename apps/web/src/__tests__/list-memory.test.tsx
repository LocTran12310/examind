import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BackLink } from "@/components/common/BackLink/BackLink";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

function List() {
  useTableQuery();
  return null;
}

describe("list memory (ui-polish AC-03)", () => {
  it("the back link returns to the page and filters the list was left on", async () => {
    setUrl("/org/bank?subject_id=s&tag_ids=nb&page=2");
    const { unmount } = render(<List />);
    unmount();
    setUrl("/org/bank/q1");
    render(<BackLink href="/org/bank">Ngân hàng câu hỏi</BackLink>);
    await waitFor(() => expect(screen.getByRole("link", { name: "← Ngân hàng câu hỏi" })).toHaveAttribute("href", "/org/bank?subject_id=s&tag_ids=nb&page=2"));
  });

  it("falls back to the plain list", () => {
    render(<BackLink href="/org/classes">Lớp học</BackLink>);
    expect(screen.getByRole("link", { name: "← Lớp học" })).toHaveAttribute("href", "/org/classes");
  });
});
