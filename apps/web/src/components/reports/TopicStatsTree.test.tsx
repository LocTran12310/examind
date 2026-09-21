import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { TopicStat } from "@/lib/types";
import { GroupStats } from "./GroupStats";
import { Heatmap, heatColor } from "./Heatmap";
import { statTree, TopicStatsTree, weakest } from "./TopicStatsTree";

const s = (id: string, parent: string | null, name: string, path: string, ratio: number, answered = 4): TopicStat => ({
  id, parent_id: parent, name, path, depth: path.split(".").length, level_kind: "topic", points: ratio * answered, max_points: answered, answered, ratio,
});
const rows = [s("gt", null, "Giải tích", "gt", 0.72), s("nh", "gt", "Nguyên hàm", "gt.nh", 0.58), s("tp", "nh", "Từng phần", "gt.nh.tp", 0.31), s("tich", "gt", "Tích phân", "gt.tich", 0.9)];

describe("reports", () => {
  it("tree shows ratios at every level and expands", () => {
    render(<TopicStatsTree rows={rows} />);
    expect(screen.getByTestId("ts-Giải tích")).toHaveTextContent("72%");
    expect(screen.getByTestId("ts-Nguyên hàm")).toHaveTextContent("58%");
    expect(screen.queryByTestId("ts-Từng phần")).toBeNull();
    fireEvent.click(screen.getByText("Nguyên hàm"));
    expect(screen.getByTestId("ts-Từng phần")).toHaveTextContent("31%");
    expect(statTree(rows)[0].children.map((c) => c.name)).toEqual(["Nguyên hàm", "Tích phân"]);
    expect(weakest(rows).map((r) => r.name)).toEqual(["Từng phần", "Tích phân"]);
  });

  it("groups use Vietnamese labels", () => {
    render(<GroupStats by="type" rows={[{ key: "mcq", label: "mcq", points: 1, max_points: 2, answered: 8, ratio: 0.5 }]} />);
    expect(screen.getByTestId("groups-type")).toHaveTextContent("Trắc nghiệm");
    expect(screen.getByTestId("groups-type")).toHaveTextContent("50%");
  });

  it("heatmap colours cells by ratio", () => {
    render(<Heatmap data={{ columns: [{ id: "c1", name: "Đại số", path: "a" }], rows: [{ student_id: "s", full_name: "An", username: "an", cells: { c1: { ratio: 1, answered: 3 } } }] }} />);
    expect(screen.getByTestId("heatmap")).toHaveTextContent("100%");
    expect(heatColor(0)).toContain("hsl(0");
    expect(heatColor(1)).toContain("hsl(120");
    expect(heatColor(null)).toBe("#f3f4f6");
  });
});
