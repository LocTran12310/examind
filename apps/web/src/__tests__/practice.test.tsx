import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PracticeButton } from "@/components/common/PracticeButton/PracticeButton";
import { ClassAdaptiveDialog } from "@/components/page-components/ClassDetail/ClassAdaptiveDialog/ClassAdaptiveDialog";
import { MyStatsPage } from "@/components/page-components/MyStats/MyStatsPage";
import { MeProvider } from "@/hooks/common/use-me";
import { mockFetch, renderWithQuery, route, me } from "./helpers";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
afterEach(() => vi.unstubAllGlobals());

describe("adaptive practice UI", () => {
  it("starts a practice exam", async () => {
    const f = mockFetch(route("POST", "/api/me/practice", { attempt_id: "att9", question_count: 20, groups: [], note: null }));
    renderWithQuery(<PracticeButton />);
    await userEvent.click(screen.getByRole("button", { name: "Tạo đề ôn tập" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/exam/att9"));
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toEqual({ count: 20 });
  });

  it("history shows why questions were chosen", async () => {
    mockFetch(
      route("GET", "/api/stats/topics", [{ id: "a", parent_id: null, name: "Đại số", path: "a", depth: 1, level_kind: "strand", points: 1, max_points: 2, answered: 8, ratio: 0.5 }]),
      route("GET", "/api/stats/groups?by=type", []),
      route("GET", "/api/me/mastery", []),
      route("GET", "/api/me/practice", [{ attempt_id: "a", title: "Đề ôn", status: "submitted", started_at: "2026-09-22T00:00:00Z", submitted_at: "", score10: 6,
      note: null, groups: [{ reason: "Chuyên đề yếu", topic: "Mệnh đề", count: 12 }, { reason: "Ôn lại câu từng làm sai", topic: null, count: 2 }] }]));
    renderWithQuery(<MeProvider value={me("student")}>
        <MyStatsPage />
      </MeProvider>);
    const h = await screen.findByTestId("practice-history");
    expect(h).toHaveTextContent("Chuyên đề yếu: Mệnh đề × 12");
    expect(h).toHaveTextContent("Ôn lại câu từng làm sai × 2");
    expect(h).toHaveTextContent("6 điểm");
  });

  it("assigns personal review exams to a class", async () => {
    const f = mockFetch(route("POST", "/api/classes/c1/adaptive-assignments", { created: 15 }));
    const onDone = vi.fn();
    renderWithQuery(<ClassAdaptiveDialog classId="c1" onDone={onDone} />);
    await userEvent.click(screen.getByRole("button", { name: "Giao đề ôn cá nhân" }));
    await waitFor(() => expect(onDone).toHaveBeenCalledWith(15));
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).toMatchObject({ count: 15, duration_minutes: 30 });
  });
});
