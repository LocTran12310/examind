import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BulkActions } from "@/components/page-components/Bank/BulkBar/BulkBar";
import type { Topic } from "@/interfaces/topic.interface";
import { mockFetch, renderWithQuery as render, route } from "./helpers";

const topics: Topic[] = [{ id: "t1", subject_id: "s", parent_id: null, name: "Vectơ", level_kind: "topic", grade: 10, path: "a", depth: 1, sort: 0, child_count: 0 }];

afterEach(() => vi.unstubAllGlobals());

describe("bulk actions", () => {
  it("disabled without selection", () => {
    render(<BulkActions ids={[]} topics={topics} tags={[]} onDone={() => {}} onClear={() => {}} />);
    expect(screen.getByRole("button", { name: /Mức độ/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Xóa" })).toBeDisabled();
  });

  it("sets difficulty and topic for the selection", async () => {
    const f = mockFetch(route("POST", "/api/questions/bulk", { updated: 2 }));
    const onDone = vi.fn();
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b"]} topics={topics} tags={[]} onDone={onDone} onClear={() => {}} />);
    await u.click(screen.getByRole("button", { name: /Mức độ/ }));
    await u.click(await screen.findByRole("menuitem", { name: "Vận dụng" }));
    await u.click(screen.getByRole("button", { name: "Chuyên đề" }));
    await u.click(within(await screen.findByRole("tree", { name: "Cây chuyên đề" })).getByText("Vectơ"));
    await waitFor(() => expect(f).toHaveBeenCalledTimes(2));
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ ids: ["a", "b"], set: { difficulty: "vd" } });
    expect(JSON.parse(String(f.mock.calls[1][1]?.body))).toEqual({ ids: ["a", "b"], set: { primary_topic_id: "t1" } });
    expect(onDone).toHaveBeenCalledTimes(2);
  });

  it("deletes each selected question after confirmation", async () => {
    const f = mockFetch(route("DELETE", "/api/questions/a", undefined, 204), route("DELETE", "/api/questions/b", { code: "question_in_use", message: "x" }, 409));
    const onClear = vi.fn();
    const u = userEvent.setup();
    render(<BulkActions ids={["a", "b"]} topics={topics} tags={[]} onDone={() => {}} onClear={onClear} />);
    await u.click(screen.getByRole("button", { name: "Xóa" }));
    expect(f).not.toHaveBeenCalled();
    await u.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xóa" }));
    await waitFor(() => expect(onClear).toHaveBeenCalled());
    expect(f).toHaveBeenCalledTimes(2);
  });
});
