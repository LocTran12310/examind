import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Topic } from "@/lib/types";
import { mockFetch, route } from "@/__tests__/helpers";
import { TopicTree } from "./TopicTree";
import { buildTree, flatten, isInSubtree } from "./tree";

const t = (id: string, name: string, parent: string | null, path: string, kind: Topic["level_kind"] = "topic"): Topic => ({
  id, subject_id: "s", parent_id: parent, name, level_kind: kind, grade: null, path, depth: path.split(".").length, sort: 0, child_count: 0,
});

const topics = [
  t("gt", "Giải tích", null, "gt", "strand"),
  t("nh", "Nguyên hàm", "gt", "gt.nh"),
  t("tp", "Tích phân", "gt", "gt.tp"),
  t("nhcb", "Nguyên hàm cơ bản", "nh", "gt.nh.nhcb", "subtopic"),
];

afterEach(() => vi.unstubAllGlobals());

describe("topic tree", () => {
  it("builds a tree and excludes the own subtree from targets", () => {
    const roots = buildTree(topics);
    expect(roots[0].children.map((c) => c.name)).toEqual(["Nguyên hàm", "Tích phân"]);
    const targets = flatten(roots).filter(({ node }) => !isInSubtree(node, topics[1]));
    expect(targets.map(({ node }) => node.name)).toEqual(["Giải tích", "Tích phân"]);
  });

  it("adds a child under a node", async () => {
    const f = mockFetch(route("POST", "/api/topics", { id: "new" }, 201));
    const onChange = vi.fn();
    render(<TopicTree topics={topics} subjectId="s" onChange={onChange} />);
    const row = screen.getByTestId("topic-Nguyên hàm");
    await userEvent.click(within(row).getByRole("button", { name: "+ Con" }));
    await userEvent.type(screen.getByPlaceholderText("Tên nhánh mới"), "Nguyên hàm từng phần");
    await userEvent.click(screen.getByRole("button", { name: "Lưu" }));
    await waitFor(() => expect(onChange).toHaveBeenCalled());
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ name: "Nguyên hàm từng phần", parent_id: "nh" });
  });

  it("shows the server refusal when deleting a node with children", async () => {
    mockFetch(route("DELETE", "/api/topics/nh", { code: "topic_has_children", message: "Chuyên đề còn nhánh con" }, 409));
    render(<TopicTree topics={topics} subjectId="s" onChange={() => {}} />);
    await userEvent.click(within(screen.getByTestId("topic-Nguyên hàm")).getByRole("button", { name: "Xóa" }));
    await userEvent.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xóa" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Chuyên đề còn nhánh con");
  });

  it("moves a node via the target picker", async () => {
    const f = mockFetch(route("POST", "/api/topics/nhcb/move", {}, 200));
    render(<TopicTree topics={topics} subjectId="s" onChange={() => {}} />);
    await userEvent.click(within(screen.getByTestId("topic-Nguyên hàm")).getByRole("button", { name: "Mở rộng" }));
    await userEvent.click(within(screen.getByTestId("topic-Nguyên hàm cơ bản")).getByRole("button", { name: "Di chuyển" }));
    const dialog = screen.getByRole("dialog");
    await userEvent.click(within(dialog).getByRole("combobox", { name: "Chuyên đề đích" }));
    await userEvent.click(await screen.findByRole("option", { name: /Tích phân$/ }));
    expect(within(dialog).getByRole("combobox", { name: "Chuyên đề đích" })).toHaveTextContent("Tích phân");
    await userEvent.click(within(dialog).getByRole("button", { name: "Di chuyển" }));
    await waitFor(() => expect(f).toHaveBeenCalled());
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ parent_id: "tp" });
  });
});
