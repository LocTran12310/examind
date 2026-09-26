import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PracticeButton } from "@/components/common/PracticeButton/PracticeButton";
import { ClassAdaptiveDialog } from "@/components/page-components/ClassDetail/ClassAdaptiveDialog/ClassAdaptiveDialog";
import { MyStatsPage } from "@/components/page-components/MyStats/MyStatsPage";
import { MeProvider } from "@/hooks/common/use-me";
import { lastBody, mockFetch, renderWithQuery, route, me } from "./helpers";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
afterEach(() => vi.unstubAllGlobals());

describe("adaptive practice UI", () => {
  const started = { attempt_id: "att9", question_count: 20, groups: [], note: null };
  const taxonomy = (...subjects: { id: string; code: string; name: string }[]) =>
    route("GET", "/api/taxonomy", { subjects, grades: [], semesters: [] });

  it("một môn thì không hỏi, nhưng đề vẫn mang môn ấy (AC-02)", async () => {
    // 0/95 đề ôn tập cũ không có môn. Trung tâm một môn thì hỏi là thừa, còn bỏ trống thì đề lại không có môn —
    // nên nó gửi thẳng môn duy nhất.
    const f = mockFetch(taxonomy({ id: "s1", code: "toan", name: "Toán" }), route("POST", "/api/me/practice", started));
    renderWithQuery(<PracticeButton />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Tạo đề ôn tập" })).toBeEnabled());
    await userEvent.click(screen.getByRole("button", { name: "Tạo đề ôn tập" }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/exam/att9"));
    expect(lastBody(f, "/me/practice")).toEqual({ count: 20, subject_id: "s1" });
  });

  it("nhiều môn thì hỏi trước, mở sẵn ở môn đang yếu nhất (AC-01)", async () => {
    const f = mockFetch(
      taxonomy({ id: "s1", code: "toan", name: "Toán" }, { id: "s2", code: "ly", name: "Vật lý" }),
      route("POST", "/api/me/practice", started),
    );
    const u = userEvent.setup();
    renderWithQuery(<PracticeButton defaultSubjectId="s2" />);
    await u.click(await screen.findByRole("button", { name: "Tạo đề ôn tập" }));
    // bước chọn mở ra ở môn yếu nhất mà trang gọi nó đã biết, không phải môn đầu bảng
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByRole("combobox", { name: "Môn ôn tập" })).toHaveTextContent("Vật lý");
    expect(push).not.toHaveBeenCalled(); // chưa tạo gì khi mới chỉ mở bước chọn
    await u.click(within(dialog).getByRole("button", { name: "Tạo đề ôn tập" }));
    await waitFor(() => expect(lastBody(f, "/me/practice")).toEqual({ count: 20, subject_id: "s2" }));
  });

  it("history shows why questions were chosen", async () => {
    mockFetch(
      route("GET", /\/api\/stats\/topics\?/, [{ id: "a", parent_id: null, name: "Đại số", path: "a", depth: 1, level_kind: "strand", points: 1, max_points: 2, answered: 8, ratio: 0.5 }]),
      route("GET", /\/api\/stats\/groups\?by=type/, []),
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
