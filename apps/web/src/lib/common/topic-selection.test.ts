import { describe, expect, it } from "vitest";
import type { Topic } from "@/interfaces/topic.interface";
import { expand, indexTree, state, toggle, topMost } from "@/lib/common/topic-selection";
import { buildTree } from "@/lib/common/topic-tree";

const t = (id: string, parent: string | null): Topic => ({ id, subject_id: "s", parent_id: parent, name: id, level_kind: "topic", grade: null, path: id, depth: 1, sort: 0, child_count: 0 });
// gt ─ nh ─ nh1, nh2 ; gt ─ tp
const ix = indexTree(buildTree([t("gt", null), t("nh", "gt"), t("nh1", "nh"), t("nh2", "nh"), t("tp", "gt"), t("hh", null)]));

describe("topic tree selection", () => {
  it("checking a parent checks the subtree and sends only the parent", () => {
    const c = toggle(ix, new Set(), "nh");
    expect([...c].sort()).toEqual(["nh", "nh1", "nh2"]);
    expect(topMost(ix, c)).toEqual(["nh"]);
    expect(state(ix, c, "gt")).toBe("indeterminate");
  });

  it("checking every child checks the parent; unchecking one child unchecks the ancestors", () => {
    let c = toggle(ix, new Set(), "nh1");
    c = toggle(ix, c, "nh2");
    expect(c.has("nh")).toBe(true);
    c = toggle(ix, c, "tp");
    expect(topMost(ix, c)).toEqual(["gt"]);
    c = toggle(ix, c, "nh2");
    expect(c.has("gt") || c.has("nh")).toBe(false);
    expect(topMost(ix, c).sort()).toEqual(["nh1", "tp"]);
  });

  it("restores the checked set from the URL form", () => {
    expect([...expand(ix, ["gt"])].sort()).toEqual(["gt", "nh", "nh1", "nh2", "tp"]);
    expect([...expand(ix, ["missing"])]).toEqual([]);
  });
});
