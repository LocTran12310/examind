import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BulkBar } from "@/components/bank/BulkBar";
import type { Topic } from "@/lib/types";
import { mockFetch, route } from "./helpers";

const topics: Topic[] = [{ id: "t1", subject_id: "s", parent_id: null, name: "Vectơ", level_kind: "topic", grade: 10, path: "a", depth: 1, sort: 0, child_count: 0 }];

afterEach(() => vi.unstubAllGlobals());

describe("bulk bar", () => {
  it("hidden without selection", () => {
    render(<BulkBar ids={[]} topics={topics} tags={[]} onDone={() => {}} onClear={() => {}} />);
    expect(screen.queryByTestId("bulk-bar")).toBeNull();
  });

  it("sets difficulty and topic for the selection", async () => {
    const f = mockFetch(route("POST", "/api/questions/bulk", { updated: 2 }));
    const onDone = vi.fn();
    render(<BulkBar ids={["a", "b"]} topics={topics} tags={[]} onDone={onDone} onClear={() => {}} />);
    await userEvent.selectOptions(screen.getByLabelText("Đặt mức độ"), "vd");
    expect(await screen.findByRole("alert")).toHaveTextContent("Đã đặt mức độ: 2 câu");
    await userEvent.click(screen.getByRole("button", { name: "Đặt chuyên đề…" }));
    await userEvent.click(within(screen.getByRole("listbox")).getByText("Vectơ"));
    await waitFor(() => expect(f).toHaveBeenCalledTimes(2));
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ ids: ["a", "b"], set: { difficulty: "vd" } });
    expect(JSON.parse(String(f.mock.calls[1][1]?.body))).toEqual({ ids: ["a", "b"], set: { primary_topic_id: "t1" } });
    expect(onDone).toHaveBeenCalledTimes(2);
  });

  it("deletes each selected question and reports failures", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mockFetch(route("DELETE", "/api/questions/a", undefined, 204), route("DELETE", "/api/questions/b", { error: { code: "question_in_use", message: "x" } }, 409));
    const onClear = vi.fn();
    render(<BulkBar ids={["a", "b"]} topics={topics} tags={[]} onDone={() => {}} onClear={onClear} />);
    await userEvent.click(screen.getByRole("button", { name: "Xóa" }));
    await waitFor(() => expect(onClear).toHaveBeenCalled());
  });
});
