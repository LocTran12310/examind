import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import MyStatsPage from "@/app/(app)/me/stats/page";
import { mockFetch, route } from "./helpers";

afterEach(() => vi.unstubAllGlobals());

describe("my stats", () => {
  it("lists weakest leaf topics first", async () => {
    mockFetch(
      route("GET", "/api/stats/topics", [
        { id: "a", parent_id: null, name: "Đại số", path: "a", depth: 1, level_kind: "strand", points: 1, max_points: 2, answered: 8, ratio: 0.5 },
        { id: "b", parent_id: "a", name: "Mệnh đề", path: "a.b", depth: 2, level_kind: "topic", points: 0.25, max_points: 1, answered: 4, ratio: 0.25 },
        { id: "c", parent_id: "a", name: "Tập hợp", path: "a.c", depth: 2, level_kind: "topic", points: 0.75, max_points: 1, answered: 4, ratio: 0.75 },
      ]),
      route("GET", "/api/stats/groups?by=type", [{ key: "mcq", label: "mcq", points: 1, max_points: 2, answered: 8, ratio: 0.5 }]),
    );
    render(<MyStatsPage />);
    const weak = await screen.findByTestId("weakest");
    expect(weak.textContent?.indexOf("Mệnh đề")).toBeLessThan(weak.textContent?.indexOf("Tập hợp") ?? 0);
    expect(weak).not.toHaveTextContent("Đại số");
  });
});
