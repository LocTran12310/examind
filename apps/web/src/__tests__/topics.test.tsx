import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Topic } from "@/interfaces/topic.interface";
import { MeProvider } from "@/app/(app)/AppShell";
import TopicsRoute from "@/app/(app)/org/topics/page";
import { TopicTree } from "@/components/page-components/Topics/TopicTree/TopicTree";
import { buildTree, flatten, isInSubtree } from "@/components/topics/tree";
import { me, mockFetch, renderWithQuery as render, route } from "./helpers";

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
    render(<TopicTree topics={topics} subjectId="s" />);
    const row = screen.getByTestId("topic-Nguyên hàm");
    await userEvent.click(within(row).getByRole("button", { name: "+ Con" }));
    await userEvent.type(screen.getByPlaceholderText("Tên nhánh mới"), "Nguyên hàm từng phần");
    await userEvent.click(screen.getByRole("button", { name: "Lưu" }));
    await waitFor(() => expect(screen.queryByPlaceholderText("Tên nhánh mới")).toBeNull()); // closes once the server accepted it
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ name: "Nguyên hàm từng phần", parent_id: "nh" });
  });

  it("shows the server refusal when deleting a node with children", async () => {
    mockFetch(route("DELETE", "/api/topics/nh", { code: "topic_has_children", message: "Chuyên đề còn nhánh con" }, 409));
    render(<TopicTree topics={topics} subjectId="s" />);
    await userEvent.click(within(screen.getByTestId("topic-Nguyên hàm")).getByRole("button", { name: "Xóa" }));
    await userEvent.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Xóa" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Chuyên đề còn nhánh con");
  });

  it("moves a node via the target picker", async () => {
    const f = mockFetch(route("POST", "/api/topics/nhcb/move", {}, 200));
    render(<TopicTree topics={topics} subjectId="s" />);
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

  it("the page shows Toán's tree and refetches it after an edit (no reload key)", async () => {
    const f = mockFetch(
      route("GET", "/api/taxonomy", { subjects: [{ id: "s-ly", code: "ly", name: "Vật lý" }, { id: "s", code: "toan", name: "Toán" }], grades: [], semesters: [] }),
      route("GET", "/api/topics?subject_id=s", topics),
      route("PATCH", "/api/topics/tp", { ...topics[2], name: "Tích phân xác định" }),
    );
    const u = userEvent.setup();
    render(
      <MeProvider value={me("teacher")}>
        <TopicsRoute />
      </MeProvider>,
    );
    const row = await screen.findByTestId("topic-Tích phân");
    const lists = () => f.mock.calls.filter(([url]) => url === "/api/topics?subject_id=s").length;
    expect(screen.getByRole("combobox", { name: "Môn học" })).toHaveTextContent("Toán");
    await u.click(within(row).getByRole("button", { name: "Đổi tên" }));
    const input = within(row).getByRole("textbox");
    await u.clear(input);
    await u.type(input, "Tích phân xác định");
    const before = lists();
    await u.click(within(row).getByRole("button", { name: "Lưu" }));
    await waitFor(() => expect(lists()).toBeGreaterThan(before)); // TOPIC_KEYS.ALL invalidated
  });

  it("students read the tree only", async () => {
    mockFetch(route("GET", "/api/taxonomy", { subjects: [{ id: "s", code: "toan", name: "Toán" }], grades: [], semesters: [] }), route("GET", "/api/topics?subject_id=s", topics));
    render(
      <MeProvider value={me("student")}>
        <TopicsRoute />
      </MeProvider>,
    );
    await screen.findByTestId("topic-Giải tích");
    expect(screen.queryByRole("button", { name: "+ Mạch kiến thức" })).toBeNull();
  });
});
