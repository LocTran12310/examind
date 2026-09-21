import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { TagManager } from "@/components/tags/TagManager";
import { mockFetch, route } from "./helpers";

afterEach(() => vi.unstubAllGlobals());

describe("tags", () => {
  it("creates a tag in a group", async () => {
    const f = mockFetch(route("POST", "/api/tags", { id: "t" }, 201));
    const onChange = vi.fn();
    render(<TagManager tags={[]} onChange={onChange} />);
    const group = screen.getByTestId("group-method");
    await userEvent.type(within(group).getByPlaceholderText("Tag mới"), "đổi biến");
    await userEvent.click(within(group).getByRole("button", { name: "Thêm" }));
    await waitFor(() => expect(onChange).toHaveBeenCalled());
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ group: "method", name: "đổi biến" });
  });

  it("shows the duplicate error", async () => {
    mockFetch(route("POST", "/api/tags", { error: { code: "conflict", message: "Tag đã tồn tại trong nhóm này" } }, 409));
    render(<TagManager tags={[{ id: "1", group: "method", name: "đổi biến" }]} onChange={() => {}} />);
    const group = screen.getByTestId("group-method");
    await userEvent.type(within(group).getByPlaceholderText("Tag mới"), "Đổi biến");
    await userEvent.click(within(group).getByRole("button", { name: "Thêm" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Tag đã tồn tại trong nhóm này");
  });

  it("renames and deletes", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const f = mockFetch(route("PATCH", "/api/tags/1", {}), route("DELETE", "/api/tags/1", undefined, 204));
    render(<TagManager tags={[{ id: "1", group: "method", name: "đổi biến" }]} onChange={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: "đổi biến" }));
    const input = screen.getByLabelText("Tên tag");
    await userEvent.clear(input);
    await userEvent.type(input, "Đổi biến số");
    await userEvent.click(screen.getByRole("button", { name: "Lưu" }));
    await waitFor(() => expect(f).toHaveBeenCalledTimes(1));
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ name: "Đổi biến số" });
  });
});
