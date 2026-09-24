import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import MyStatsPage from "@/app/(app)/me/stats/page";
import { MeProvider } from "@/hooks/common/use-me";
import { mockFetch, renderWithQuery as render, route, me } from "./helpers";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

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
      route("GET", "/api/me/practice", []),
      route("GET", "/api/me/mastery", [
        { topic_id: "a", parent_id: null, name: "Đại số", path: "a", depth: 1, mastery: 0.5, answers: 12, tracked: false, enough_data: true, weak: false },
        { topic_id: "b", parent_id: "a", name: "Mệnh đề", path: "a.b", depth: 2, mastery: 0.3, answers: 6, tracked: true, enough_data: true, weak: true },
        { topic_id: "c", parent_id: "a", name: "Tập hợp", path: "a.c", depth: 2, mastery: 0.7, answers: 6, tracked: true, enough_data: true, weak: false },
      ]),
    );
    render(<MeProvider value={me("student")}>
        <MyStatsPage />
      </MeProvider>);
    const weak = await screen.findByTestId("mastery");
    expect(weak.textContent?.indexOf("Mệnh đề")).toBeLessThan(weak.textContent?.indexOf("Tập hợp") ?? 0);
    expect(weak).not.toHaveTextContent("Đại số");
  });
});
